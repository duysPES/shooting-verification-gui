mod lib;
use bytes::BytesMut;
use lib::{ConnMode, ConnPackage, InfoType, Message};
use std::error::Error;
use std::io;
use std::io::{Read, Write};
use std::net::{Shutdown, TcpListener, TcpStream};
use std::thread;

static LISC_ADDR: &'static str = "127.0.0.1:8001";

fn get_utf8(stream: &mut TcpStream) -> io::Result<String> {
    let mut buf = [0 as u8; 50];

    if let Ok(n) = stream.read(&mut buf) {
        if n < 2 {
            return Ok("".to_string());
        }
        let resp = String::from_utf8(Vec::from(&buf[0..n - 2])).unwrap_or("".to_string());
        Ok(resp)
    } else {
        Ok("".to_string())
    }
}

fn main() -> Result<(), Box<dyn Error>> {
    let mode = ConnMode::Debug;
    let info = InfoType::Other;
    let msg = Message::Status((0, [1, 2, 3], [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10]));
    let package = ConnPackage::create(info, mode, msg);
    // let lisc = TcpListener::bind(LISC_ADDR)?;

    // println!("LISC server listening on {}", LISC_ADDR);

    // for incoming in lisc.incoming() {
    //     match incoming {
    //         Ok(mut stream) => {
    //             let resp = get_utf8(&mut stream)?;

    //             let split_string: Vec<&str> = resp.split(",").collect();
    //             println!("{:?}", split_string);

    //             if let Some(start) = split_string.first() {
    //                 match start {
    //                     &"START" => {
    //                         stream.write(b"OK")?;
    //                         let _ = thread::spawn(move || {
    //                             inventory(stream).unwrap_or_else(|e| {
    //                                 println!("Inventory errored out with error={:?}", e);
    //                             });
    //                         });
    //                     }
    //                     _ => (),
    //                 }
    //             }
    //         }
    //         Err(e) => {
    //             println!("Error: {}", e);
    //         }
    //     }
    // }
    Ok(())
}

pub fn inventory(mut socket: TcpStream) -> std::io::Result<()> {
    println!("Starting inventory process piping too: {:?}", socket);
    let done = "DONE".as_bytes();
    socket.write(done)?;
    Ok(())
}
