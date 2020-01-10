use crate::switch::Switch;
use bytes::BytesMut;
use lazy_static::lazy_static;
use serialport::prelude::*;
use std::collections::HashMap;
use std::io;
use std::io::{Read, Write};
use std::net::TcpStream;
use std::thread;
use std::time::Duration;

#[derive(Debug, Clone)]
pub enum Message {
    String(String),                   // basic string message
    Switch((u8, BytesMut)),           // position, address
    Status((u8, BytesMut, BytesMut)), // position, address, status_packet
}

lazy_static! {
    static ref LISC_CMDS: HashMap<&'static str, BytesMut> = {
        let mut lisc_cmds = HashMap::new();
        lisc_cmds.insert("zl", BytesMut::from("zl".as_bytes()));
        lisc_cmds.insert("zL", BytesMut::from("zL".as_bytes()));
        lisc_cmds
    };
}

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

pub struct ConnPackage {
    info: InfoType,
    mode: ConnMode,
    msg: Message,
}

impl<'a> ConnPackage {
    pub fn debug(socket: &mut Socket, msg: &'a str) -> serialport::Result<()> {
        let msg = Message::String(msg.into());
        ConnPackage::new(InfoType::Other, ConnMode::Debug, msg).send(socket)?;
        Ok(())
    }

    pub fn done(socket: &mut Socket) -> serialport::Result<()> {
        let done_msg = Message::String("".into());
        ConnPackage::new(InfoType::Kill, ConnMode::Debug, done_msg).send(socket)?;
        Ok(())
    }

    pub fn switch(socket: &mut Socket, pos: u8, switch: &Switch) -> serialport::Result<()> {
        let switch_msg = Message::Switch((pos, switch.address()));
        ConnPackage::new(InfoType::Switch, ConnMode::Main, switch_msg).send(socket)?;
        Ok(())
    }

    fn new(infotype: InfoType, mode: ConnMode, msg: Message) -> Self {
        Self {
            info: infotype,
            mode: mode,
            msg: msg,
        }
    }

    fn send(self, socket: &mut Socket) -> serialport::Result<()> {
        let data = self.create();
        socket.write_with_delay(&data[..], 10)?;
        Ok(())
    }

    fn create(&self) -> BytesMut {
        let package = format!("{:?},{:?}", self.info, self.mode);

        match self.msg.clone() {
            Message::String(msg) => {
                let package = format!("{},{}", package, msg);
                BytesMut::from(package.as_str())
            }
            Message::Switch((pos, addr)) => {
                let package = format!("{},{},{:?}", package, pos, BytesMut::from(&addr[..]));
                BytesMut::from(package.as_str())
            }
            Message::Status((pos, addr, status)) => {
                let package = format!(
                    "{},{},{:?},{:?}",
                    package,
                    pos,
                    BytesMut::from(&addr[..]),
                    BytesMut::from(&status[..])
                );
                BytesMut::from(package.as_str())
            }
        }
    }
}

pub struct Socket {
    pub stream: TcpStream,
}

impl Socket {
    pub fn new(stream: TcpStream) -> Self {
        Self { stream: stream }
    }

    pub fn get_utf8(&mut self) -> io::Result<String> {
        let mut buf = [0 as u8; 50];

        if let Ok(n) = self.stream.read(&mut buf) {
            if n < 2 {
                return Ok("".to_string());
            }
            let resp = String::from_utf8(Vec::from(&buf[0..n - 2])).unwrap_or("".to_string());
            Ok(resp)
        } else {
            Ok("".to_string())
        }
    }

    pub fn write_with_delay(&mut self, buf: &[u8], delay_ms: u64) -> io::Result<()> {
        self.stream.write(buf)?;
        thread::sleep(Duration::from_millis(delay_ms));
        Ok(())
    }
}

pub struct Lisc {
    pub serial: Box<dyn SerialPort>,
}

impl Lisc {
    pub fn new() -> serialport::Result<Self> {
        let serial = serialport::open("COM6")?;

        Ok(Self { serial: serial })
    }

    pub fn listen(&mut self, expected_length: usize) -> serialport::Result<BytesMut> {
        let mut buf: Vec<u8> = Vec::with_capacity(expected_length);
        let n = self.serial.read(buf.as_mut_slice())?;

        Ok(BytesMut::from(&buf[0..n]))
    }

    pub fn listen_broadcast(
        &mut self,
        socket: &mut Socket,
        mut tries: u8,
        expected_length: usize,
    ) -> serialport::Result<BytesMut> {
        let msg = format!("Listening for broadcast [{}] tries", tries);
        ConnPackage::debug(socket, msg.as_str())?;
        self.listen(expected_length)
    }

    pub fn write(&mut self, data: &BytesMut) -> serialport::Result<()> {
        self.serial.write(&data[..])?;
        Ok(())
    }

    pub fn write_with_delay(&mut self, data: &BytesMut, delay_ms: u64) -> serialport::Result<()> {
        self.serial.write(&data[..])?;
        thread::sleep(Duration::from_millis(delay_ms));
        Ok(())
    }

    pub fn reset(&mut self) -> serialport::Result<()> {
        self.write_with_delay(LISC_CMDS.get(&"zl").unwrap(), 100)?;
        self.write_with_delay(LISC_CMDS.get(&"zL").unwrap(), 100)?;
        Ok(())
    }
}
