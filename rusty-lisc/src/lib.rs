use bytes::BytesMut;
use std::net::TcpStream;

#[derive(Debug)]
pub enum ConnMode {
    Debug,
    Main,
    Staus,
}

#[derive(Debug)]
pub enum InfoType {
    Switch,
    Other,
    Kill,
}

pub enum Message {
    String(String),                  // basic string message
    Switch((u8, [u8; 3])),           // position, address
    Status((u8, [u8; 3], [u8; 11])), // position, address, status_packet
}

pub struct ConnPackage;

impl ConnPackage {
    pub fn create(infotype: InfoType, mode: ConnMode, msg: Message) -> () {
        let package = format!("{:?},{:?}", infotype, mode);

        match msg {
            Message::String(msg) => {
                let package = format!("{},{}", package, msg);
                println!("{}", package);
            }
            Message::Switch((pos, addr)) => {
                let package = format!("{},{:?}", pos, BytesMut::from(&addr[..]));
                println!("{}", package);
            }
            Message::Status((pos, addr, status)) => {
                let package = format!(
                    "{},{:?},{:?}",
                    pos,
                    BytesMut::from(&addr[..]),
                    BytesMut::from(&status[..])
                );
                println!("{}", package);
            }
        }
    }
}
