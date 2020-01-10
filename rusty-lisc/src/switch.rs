use bytes::BytesMut;
use std::error;
use std::fmt;

#[derive(Debug, Clone)]
pub enum SwitchError {
    InvalidRawLength,
}

impl fmt::Display for SwitchError {
    fn fmt(&self, f: &mut fmt::Formatter) -> fmt::Result {
        write!(f, "Switch Error")
    }
}

impl error::Error for SwitchError {
    fn source(&self) -> Option<&(dyn error::Error + 'static)> {
        None
    }
}

type SwitchResult<T> = std::result::Result<T, SwitchError>;

pub struct Switch {
    inner: BytesMut,
    length: usize,
}

impl<'a> Switch {
    pub fn from_raw(raw: &'a [u8]) -> SwitchResult<Self> {
        if raw.len() < 5 {
            return Err(SwitchError::InvalidRawLength);
        }
        Ok(Self {
            inner: BytesMut::from(raw),
            length: raw.len() - 1,
        })
    }

    pub fn address(&self) -> BytesMut {
        BytesMut::from(&self.inner[0..2])
    }

    pub fn package(&self) -> BytesMut {
        BytesMut::from(&self.inner[2..self.length])
    }

    pub fn checksum(&self) -> BytesMut {
        let mut buf: Vec<u8> = Vec::with_capacity(1);
        buf.push(self.inner[self.length]);
        BytesMut::from(&buf[..])
    }
}
