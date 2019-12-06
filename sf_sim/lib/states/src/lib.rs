use bytes::{BufMut, BytesMut};
use rand::RandSwitchMetric;

pub static SWITCH_ADDR: &[u16] = &[0x1aff, 0x2bfe, 0x3cfd, 0x4dfc];

#[derive(Debug)]
pub struct SwitchStatus {
    random: RandSwitchMetric,
    volts: u8,
    temp: u8,
    detd: u8,
    perror: u8,
    cerror: u8,
    nfire: u8,
    flags: u8,
}

impl SwitchStatus {
    pub fn new() -> Self {
        SwitchStatus {
            random: RandSwitchMetric {},
            volts: 0,
            temp: 0,
            detd: 0,
            perror: 0,
            cerror: 0,
            nfire: 0,
            flags: 0,
        }
    }

    pub fn generate(&mut self) -> BytesMut {
        let mut packet = BytesMut::with_capacity(7);
        let volt = self.random.voltage();
        let temp = self.random.temp();
        packet.put_u8(volt);
        packet.put_u8(temp);
        packet.put_u8(self.detd);
        packet.put_u8(self.perror);
        packet.put_u8(self.cerror);
        packet.put_u8(self.nfire);
        packet.put_u8(self.random.rand());
        packet
    }

    pub fn chksum_error(&mut self, amt: u8) {
        self.cerror += amt;
    }

    pub fn packet_errors(&mut self, amt: u8) {
        self.perror += amt;
    }
}

#[derive(Debug)]
pub enum Commands {
    ACK,
    NACK,
    GetStatus,
    GoIdle,
    InvalidCmd,
}

impl Commands {
    pub fn value(&self) -> BytesMut {
        match *self {
            Commands::ACK => BytesMut::from(&b"\x06"[..]),
            Commands::NACK => BytesMut::from(&b"\x15"[..]),
            Commands::GetStatus => BytesMut::from(&b"\x05"[..]),
            Commands::GoIdle => BytesMut::from(&b"\x1e"[..]),
            Commands::InvalidCmd => BytesMut::from(&b"\x00"[..]),
        }
    }
    pub fn from_bytes(bytes: &[u8]) -> Self {
        match bytes {
            b"\x06" => Commands::ACK,
            b"\x15" => Commands::NACK,
            b"\x05" => Commands::GetStatus,
            b"\x1e" => Commands::GoIdle,
            _ => Commands::InvalidCmd,
        }
    }
}

#[derive(Debug)]
pub enum SwitchStates {
    GoInactive,
    GetStatus,
    Broadcast,
    NULL,
}

impl SwitchStates {
    pub fn value(&self) -> &'static str {
        match *self {
            SwitchStates::GoInactive => "GoInactive",
            SwitchStates::GetStatus => "GetStatus",
            SwitchStates::Broadcast => "Broadcasting",
            SwitchStates::NULL => "NULL",
        }
    }
}

#[derive(Debug)]
pub struct Switch {
    pub id: u16,
    pub status: SwitchStatus,
}

impl Switch {
    pub fn new(id: u16) -> Self {
        Switch {
            id: id,
            status: SwitchStatus::new(),
        }
    }

    ///
    /// Simulate an ACK packet
    /// [id][ack][chksum]
    ///
    pub fn gen_ack(&self) -> BytesMut {
        self.gen_command(&Commands::ACK.value())
    }

    pub fn gen_nack(&self) -> BytesMut {
        self.gen_command(&Commands::NACK.value())
    }

    pub fn gen_status_response(&mut self) -> BytesMut {
        let response = self.status.generate();
        self.gen_command(&response)
    }

    fn gen_command(&self, cmd: &BytesMut) -> BytesMut {
        let mut packet = BytesMut::new();
        let addr = BytesMut::from(&self.id.to_be_bytes()[..]);

        packet.extend_from_slice(&addr[..]);
        packet.extend_from_slice(&cmd[..]);

        let chksum = self.gen_chksum(&packet);

        packet.extend_from_slice(&chksum[..]);
        packet
    }

    fn gen_chksum(&self, packet: &BytesMut) -> BytesMut {
        let mut chksum = BytesMut::from(&b"\x00"[..]);

        for (idx, byte) in packet.iter().enumerate() {
            if idx == packet.len() - 1 {
                break;
            }

            chksum[0] ^= byte;
        }
        BytesMut::from(&chksum[..])
    }
}

#[derive(Debug)]
pub struct SwitchStateMachine {
    pub state: SwitchStates,
    pub switch: Switch,
}

impl SwitchStateMachine {
    pub fn new(id: u16) -> Self {
        let first_switch = Switch::new(id);
        SwitchStateMachine {
            state: SwitchStates::Broadcast,
            switch: first_switch,
        }
    }

    pub fn null() -> Self {
        SwitchStateMachine {
            state: SwitchStates::NULL,
            switch: Switch::new(0),
        }
    }

    pub fn to_broadcast_state(&mut self) -> Result<(), String> {
        if let SwitchStates::NULL = self.state {
            self.state = SwitchStates::Broadcast
        } else {
            return Err("Incorrect switch transition".to_owned());
        }
        Ok(())
    }

    pub fn to_status_state(&mut self) -> Result<(), String> {
        if let SwitchStates::Broadcast = self.state {
            self.state = SwitchStates::GetStatus
        } else {
            return Err("Incorrect switch transition".to_owned());
        }

        Ok(())
    }

    pub fn to_inactive_state(&mut self) -> Result<(), String> {
        self.state = match self.state {
            SwitchStates::Broadcast => SwitchStates::GoInactive,
            SwitchStates::GetStatus => SwitchStates::GoInactive,
            _ => {
                return Err("Incorrect switch transition".to_owned());
            }
        };
        Ok(())
    }

    pub fn next_state(&mut self) -> Result<(), String> {
        match self.state {
            SwitchStates::NULL => self.state = SwitchStates::Broadcast,
            SwitchStates::Broadcast => self.state = SwitchStates::GetStatus,
            SwitchStates::GetStatus => self.state = SwitchStates::GoInactive,
            SwitchStates::GoInactive => self.state = SwitchStates::Broadcast,
        }
        Ok(())
    }

    pub fn change_switch(&mut self, new_switch: Switch) -> Result<(), String> {
        self.switch = new_switch;
        self.state = SwitchStates::Broadcast;

        Ok(())
    }
}

#[cfg(test)]
mod tests {
    use super::*;
}
