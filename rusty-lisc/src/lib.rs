use bytes::BytesMut;
use lazy_static::lazy_static;
use serialport::prelude::*;
use std::collections::HashMap;
use std::io;
use std::io::{Read, Write};
use std::net::TcpStream;
use std::thread;
use std::time::Duration;

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

pub enum Message {
    String(String),                  // basic string message
    Switch((u8, [u8; 3])),           // position, address
    Status((u8, [u8; 3], [u8; 11])), // position, address, status_packet
}

pub struct ConnPackage;

impl<'a> ConnPackage {
    pub fn create(infotype: InfoType, mode: ConnMode, msg: Message) -> BytesMut {
        let package = format!("{:?},{:?}", infotype, mode);

        match msg {
            Message::String(msg) => {
                let package = format!("{},{}", package, msg);
                BytesMut::from(package.as_str())
            }
            Message::Switch((pos, addr)) => {
                let package = format!("{},{:?}", pos, BytesMut::from(&addr[..]));
                BytesMut::from(package.as_str())
            }
            Message::Status((pos, addr, status)) => {
                let package = format!(
                    "{},{:?},{:?}",
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

    pub fn write_with_delay(&mut self, buf: &[u8], delay: Duration) -> io::Result<()> {
        self.stream.write(buf)?;
        thread::sleep(delay);
        Ok(())
    }
}

pub struct Lisc {
    pub serial: Box<dyn SerialPort>,
}

impl Lisc {
    pub fn new() -> serialport::Result<Self> {
        let serial = serialport::open("/dev/ttyS7")?;

        Ok(Self { serial: serial })
    }

    pub fn listen(&mut self) -> serialport::Result<BytesMut> {
        let mut buf: Vec<u8> = Vec::with_capacity(64);
        let n = self.serial.read(buf.as_mut_slice())?;

        Ok(BytesMut::from(&buf[0..n]))
    }

    pub fn write(&mut self, data: &BytesMut) -> serialport::Result<()> {
        self.serial.write(&data[..])?;
        Ok(())
    }

    pub fn write_with_delay(&mut self, data: &BytesMut, with_delay: u64) -> serialport::Result<()> {
        self.serial.write(&data[..])?;
        thread::sleep(Duration::from_millis(with_delay));
        Ok(())
    }

    pub fn reset(&mut self) -> serialport::Result<()> {
        self.write_with_delay(LISC_CMDS.get(&"zl").unwrap(), 100)?;
        self.write_with_delay(LISC_CMDS.get(&"zL").unwrap(), 100)?;
        Ok(())
    }
}
