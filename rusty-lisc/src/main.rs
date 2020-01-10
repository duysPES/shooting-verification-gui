mod comms;
mod switch;

use bytes::BytesMut;
use comms::{ConnMode, ConnPackage, InfoType, Lisc, Message, Socket};
use std::error::Error;
use std::io;
use std::io::Write;
use std::net::{Shutdown, TcpListener};
use std::thread;
use std::time::Duration;
use switch::Switch;

static LISC_ADDR: &'static str = "127.0.0.1:8001";

fn main() -> serialport::Result<()> {
    let lisc = TcpListener::bind(LISC_ADDR)?;
    println!("LISC server listening on {}", LISC_ADDR);

    for incoming in lisc.incoming() {
        match incoming {
            Ok(mut stream) => {
                let s = stream.try_clone()?;
                let mut socket = Socket::new(s);
                let resp = socket.get_utf8()?;

                let split_string: Vec<&str> = resp.split(",").collect();
                let expected_switches = *split_string.get(1).unwrap();
                let expected_switches = expected_switches.to_string().parse::<u64>().unwrap();

                if let Some(start) = split_string.first() {
                    match start {
                        &"START" => {
                            stream.write(b"OK")?;
                            let _ = thread::spawn(move || {
                                inventory(socket, expected_switches).unwrap_or_else(|e| {
                                    println!("Inventory errored out with error={:?}", e);
                                });
                            });
                        }
                        _ => (),
                    }
                }
            }
            Err(e) => {
                println!("Error: {}", e);
            }
        }
    }
    Ok(())
}

pub fn inventory(mut socket: Socket, expected_switches: u64) -> serialport::Result<()> {
    let lisc = Lisc::new();

    match lisc {
        Ok(mut lisc) => {
            // lisc has successfully connected! Now do the actual inventory!
            lisc.reset()?;
            ConnPackage::debug(&mut socket, "Resetting LISC")?;

            'switch_loop: for switch in 0..expected_switches {
                {
                    'broadcast_loop: for k in 0..5 {
                        if k == 4 {
                            ConnPackage::debug(
                                &mut socket,
                                "Inventory terminating broadcasting not recieving",
                            )?;

                            socket
                                .stream
                                .shutdown(Shutdown::Both)
                                .expect("Shutdown call failed");
                            panic!("Broadcast failed terminating server..")
                        }
                        let resp =
                            lisc.listen_broadcast(&mut socket, k + 1, 5)
                                .unwrap_or_else(|e| {
                                    let err_msg = format!("ERR: {}", e);
                                    ConnPackage::debug(&mut socket, err_msg.as_str())
                                        .expect("Error sending to socket");
                                    BytesMut::new()
                                });
                        if resp.len() > 0 {
                            break 'switch_loop;
                        } else {
                            continue 'broadcast_loop;
                        }
                    }
                }

                break;
            }
            // let switch = Switch::from_raw(b"\x00\x01\x02\x03\x04\x05").unwrap();
            // ConnPackage::switch(&mut socket, 1, &switch)?;
            socket.write_with_delay(b"DONE", 1)?;
            Ok(())
        }
        Err(e) => Err(e),
    }

    // let package = ConnPackage::create(
    //     InfoType::Other,
    //     ConnMode::Main,
    //     Message::String("Switch is not okay!".to_string()),
    // );
    // socket.write_with_delay(&package[..], Duration::from_millis(10))?;
    // socket.stream.write(b"DONE")?;
    // Ok(())
}
