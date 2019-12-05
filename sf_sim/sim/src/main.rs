#![allow(dead_code)]

use states::SwitchStates;
use states::*;
use std::error::Error;
use std::fmt::{Debug, Display};
use std::net::Shutdown;
use std::string::ToString;
use std::time::Duration;
use tokio;
use tokio::io::{AsyncReadExt, AsyncWriteExt};
use tokio::net::{TcpListener, TcpStream};
use tokio::time;

async fn send_addr_state(stream: &mut TcpStream, addr: &u16, state: &SwitchStateMachine) {
    // let mut msg: String = String::new();
    // msg.push_str(&addr.to_string());
    // msg.push_str(",");
    // msg.push_str(format!("{:?}", state.state));
    let msg = format!("{},{:?}", addr, state.state);

    let _ = stream.write_all(nl(msg).as_bytes()).await.unwrap();
}

async fn send_raw(stream: &mut TcpStream, msg: Vec<u8>) {
    let _ = stream.write_all(&msg[..]).await.unwrap();
}

fn nl(mut msg: String) -> String {
    msg.push_str("\n");
    msg
}

// async fn do_broadcast(stream: &mut TcpStream, state_machine: &SwitchStateMachine) {
//     let mut cnt: usize = 0;

//     let msg = nl(state_machine.switch.id.to_string());
//     while cnt < 1 {
//         time::delay_for(Duration::from_secs(2)).await;
//         let _ = stream
//             .write_all(msg.as_bytes())
//             .await
//             .expect("Couldn't write to stream");
//         cnt += 1;
//     }
// }

async fn process_client(mut stream: TcpStream) -> bool {
    let mut data = [0 as u8; 50]; // using 50 byte buffer

    let mut state_machine: SwitchStateMachine = SwitchStateMachine::null();
    let mut addr: u16 = 0;
    let mut state = format!("{:?}", SwitchStates::NULL);
    let mut cur_switch = 0;

    'main: while match stream.read(&mut data).await {
        Ok(size) => {
            // echo everything!

            // let msg_hex = &data[0..size];
            let msg_string = String::from_utf8_lossy(&data[0..size]);
            if size == 0 {
                println!(
                    "Done with client, terminating connection [{}]",
                    stream.peer_addr().unwrap()
                );
                stream.shutdown(Shutdown::Both).unwrap();
                return false;
            }
            println!("MSG: [{}], size: {}", msg_string, size);

            if msg_string == "begin_inventory" {
                let first_switch = Switch::new(SWITCH_ADDR[cur_switch]);
                state_machine
                    .change_switch(first_switch)
                    .expect("Could not initialize first switch");

                time::delay_for(Duration::from_secs(2)).await;
                send_raw(&mut stream, state_machine.switch.gen_nack()).await;

                // do_broadcast(&mut stream, &addr).await;
                // for id in SWITCH_ADDR.iter() {
                //     // will explicitly go from NULL -> Broadcasting
                //     state_machine
                //         .next_state()
                //         .expect("Something went wrong with state transitions");
                //     // Broadcasting switch....
                //     let new_switch = Switch::new(*id);
                //     state_machine
                //         .change_switch(new_switch)
                //         .expect("Couldn't create new switch");

                //     addr = state_machine.switch.id;
                //     send_addr_state(&mut stream, &addr, &state_machine).await;
                // }
            }

            // if msg_string == "test" {
            //     println!("Sending test response");
            //     stream
            //         .write_all(b"Sending while doing other things, server side\n")
            //         .await
            //         .expect("Couldn't write to client");
            //     continue 'main;
            // }

            // if addr > 0 {
            //     match &state_machine.state {
            //         SwitchStates::Broadcast => {
            //             send_addr_state(&mut stream, &addr, &state).await;
            //             do_broadcast(&mut stream, &addr).await;
            //             state_machine.to_status_state().unwrap();
            //         }

            //         SwitchStates::GetStatus => {
            //             send_addr_state(&mut stream, &addr, &state).await;
            //             state_machine.to_inactive_state().unwrap();
            //         }
            //         SwitchStates::GoInactive => {
            //             send_addr_state(&mut stream, &addr, &state).await;
            //             if idx == SWITCH_ADDR.len() - 1 {
            //                 return;
            //             }
            //             idx += 1;
            //             state_machine.change_switch(idx).unwrap();
            //         }
            //         _ => panic!("This shouldn't print"),
            //     }
            // }

            true
        }
        Err(_) => {
            println!(
                "An error occurred, terminating connection with {}",
                stream.peer_addr().unwrap()
            );
            false
        }
    } {}

    false
}

#[tokio::main]
async fn main() -> Result<(), Box<dyn Error>> {
    let mut listener = TcpListener::bind("127.0.0.1:8000").await?;
    // accept connections and process them, spawning a new thread for each one
    println!("Server listening on port 8000");

    loop {
        let (mut stream, _) = listener.accept().await?;

        tokio::spawn(async move {
            let _ = stream
                .write_all(b"Connected Established")
                .await
                .expect("Couldn't write to client");

            process_client(stream).await;
        });
    }
    // match stream {
    //     Ok(mut stream) => {
    //         println!("New connection: {}", stream.peer_addr().unwrap());
    //         thread::spawn(move || {
    //             // connection succeeded
    //             stream.write(b"Server connected succesfully\r\n").unwrap();

    //             // create new statemachine for client
    //             process_client(stream)
    //         });
    //     }
    //     Err(e) => {
    //         println!("Error: {}", e);
    //         /* connection failed */
    //     }
    // }
}
