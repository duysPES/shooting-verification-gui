#![allow(dead_code)]
#![allow(unused_variables)]

use bytes::{BufMut, BytesMut};
use states::{Commands, Switch, SwitchStateMachine, SWITCH_ADDR};
use std::error::Error;
use std::net::Shutdown;
use std::time::Duration;
use tokio;
use tokio::io::{AsyncReadExt, AsyncWriteExt};
use tokio::net::{TcpListener, TcpStream};
use tokio::time;

struct ClientHandler {
    state_machine: SwitchStateMachine,
}

impl ClientHandler {
    fn new() -> Self {
        let state_machine = SwitchStateMachine::null();
        ClientHandler {
            state_machine: state_machine,
        }
    }

    fn change_switch(&mut self, new_switch: Switch) -> Result<(), String> {
        self.state_machine
            .change_switch(new_switch)
            .expect("Could not change switches internally");

        Ok(())
    }

    fn parse_packet(&self, mut input: &mut BytesMut) -> Commands {
        let (addr, body, chksum) = self.split_packet(&mut input);
        let result = Commands::from_bytes(&body);
        // println!("{:?}", result);
        result
    }

    fn split_packet(&self, packet: &mut BytesMut) -> (BytesMut, BytesMut, BytesMut) {
        // println!("{:?}", packet);
        let addr = packet.split_to(3);
        let chksum = packet.split_off(packet.len() - 1);
        let body = packet.clone();
        (addr, body, chksum)
    }

    fn to_bytes(&self, string: &[u8]) -> BytesMut {
        BytesMut::from(&string[..])
    }

    fn check_chksum(&self, packet: &BytesMut) -> bool {
        let mut chksum: u8 = 0;

        for (idx, byte) in packet.iter().enumerate() {
            if idx == packet.len() - 1 {
                break;
            }

            chksum ^= byte;
        }
        chksum == packet[packet.len() - 1]
    }

    async fn write(&mut self, stream: &mut TcpStream, msg: &[u8]) {
        let _ = stream.write_all(msg).await.unwrap();
        time::delay_for(Duration::from_millis(100)).await;
    }

    async fn send_raw(&mut self, stream: &mut TcpStream, msg: BytesMut) {
        let _ = stream.write_all(&msg[..]).await.unwrap();
    }

    async fn send(&mut self, mut stream: &mut TcpStream, cmd: Commands) {
        // time::delay_for(Duration::from_secs(2)).await;
        // client_handler.send_nack(&mut stream).await;
        // time::delay_for(Duration::from_millis(100)).await;
        // client_handler.send_state(&mut stream).await;
        time::delay_for(Duration::from_secs(1)).await;
        match cmd {
            Commands::ACK => {
                self.send_raw(&mut stream, self.state_machine.switch.gen_nack())
                    .await;
            }
            Commands::NACK => {
                self.send_raw(&mut stream, self.state_machine.switch.gen_nack())
                    .await;
            }
            Commands::GetStatus => {
                let switch_status = self.state_machine.switch.gen_status_response();
                println!("{:?}", switch_status);
                self.send_raw(&mut stream, switch_status).await;
            }
            _ => (),
        }

        time::delay_for(Duration::from_millis(100)).await;
        self.send_state(&mut stream).await;
        time::delay_for(Duration::from_secs(1)).await;
    }

    fn nl(&self, mut msg: String) -> String {
        msg.push_str("\n");
        msg
    }

    async fn send_state(&self, stream: &mut TcpStream) {
        let state = self.state_machine.state.value();

        let _ = stream.write_all(state.as_bytes()).await.unwrap();
    }
}

async fn process_client(mut stream: TcpStream) -> bool {
    let mut data = [0 as u8; 50]; // using 50 byte buffer

    let mut cur_switch = 0;

    let mut client_handler = ClientHandler::new();

    'main: while match stream.read(&mut data).await {
        Ok(size) => {
            // echo everything!

            // let msg_hex = &data[0..size];
            let msg_string = String::from_utf8_lossy(&data[0..size]);
            if size == 0 {
                // sending null packets - client disconnected

                println!(
                    "Done with client, terminating connection [{}]",
                    stream.peer_addr().unwrap()
                );
                stream.shutdown(Shutdown::Both).unwrap();
                return false;
            } else if size == 5 {
                let data = &data[0..size];
                let mut byte_string = client_handler.to_bytes(data);
                // println!("{:?}", byte_string);
                // first check chksum
                if !client_handler.check_chksum(&byte_string) {
                    // handle what happens if checksum comes back wrong
                    println!("Checksum is wrong!");
                }
                let result = match client_handler.parse_packet(&mut byte_string) {
                    Commands::GetStatus => {
                        //
                        println!("It made it here!");
                        // client_handler.write(&mut stream, b"Sending Status..").await;
                        client_handler.state_machine.next_state().unwrap();
                        client_handler.send(&mut stream, Commands::GetStatus).await;
                    }
                    Commands::GoIdle => {
                        //
                        // client_handler.write(&mut stream, b"Going Idle").await;
                        client_handler.state_machine.next_state().unwrap();
                        client_handler.send(&mut stream, Commands::ACK).await;
                        // done with this switch, move on to next one
                        cur_switch += 1;

                        if cur_switch == SWITCH_ADDR.len() {
                            client_handler
                                .write(&mut stream, b"Simulation DONE!!!")
                                .await;
                        } else {
                            let next_switch = Switch::new(SWITCH_ADDR[cur_switch]);
                            client_handler
                                .change_switch(next_switch)
                                .expect("Could not move on to next switch");
                            client_handler.send(&mut stream, Commands::NACK).await;
                        }
                    }
                    _ => panic!(format!("This shouldn't happen; packet: {:?}", byte_string)),
                };

            // check to make sure chksum if correct...
            } else {
                // other type of incoming information
                println!("MSG: [{}]", msg_string);
            }

            if msg_string == "begin_inventory" {
                cur_switch = 0;
                let first_switch = Switch::new(SWITCH_ADDR[cur_switch]);

                client_handler
                    .change_switch(first_switch)
                    .expect("Could not change first switch");
                client_handler.send(&mut stream, Commands::NACK).await;
            }

            if msg_string == "quit_server" {
                return false;
            }

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
                .write_all(b"Connection Established")
                .await
                .expect("Couldn't write to client");

            process_client(stream).await;
        });
    }
    println!("Shutting down server");
}
