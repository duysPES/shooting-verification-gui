mod lib;
use lib::{ConnMode, ConnPackage, InfoType, Lisc, Message, Socket};
use std::error::Error;
use std::io;
use std::io::Write;
use std::net::{Shutdown, TcpListener};
use std::thread;
use std::time::Duration;
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
                println!("{:?}", split_string);

                if let Some(start) = split_string.first() {
                    match start {
                        &"START" => {
                            stream.write(b"OK")?;
                            let _ = thread::spawn(move || {
                                inventory(socket).unwrap_or_else(|e| {
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

pub fn inventory(socket: Socket) -> serialport::Result<()> {
    let lisc = Lisc::new();

    match lisc {
        Ok(mut lisc) => {
            // lisc has successfully connected! Now do the actual inventory!
            lisc.reset()?;
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
