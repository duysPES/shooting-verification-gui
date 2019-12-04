use std::error::Error;

pub static SWITCH_ADDR: &[u16] = &[0x1aff, 0x2bfe, 0x3cfd, 0x4dfc];

#[derive(Debug)]
pub enum SwitchStates {
    GoInactive,
    GetStatus,
    Broadcast,
    NULL,
}

#[derive(Debug)]
pub struct Switch {
    pub id: u16,
}

impl Switch {
    #[inline]
    pub fn ACK() -> u8 {
        0x05
    }

    #[inline]
    pub fn NACK() -> u8 {
        0x15
    }

    pub fn new(id: u16) -> Self {
        Switch { id: id }
    }

    ///
    /// Simulate an ACK packet
    /// [id][ack][chksum]
    ///
    pub fn gen_ack(&self) -> Vec<u8> {
        let mut packet: Vec<u8> = Vec::new();

        packet.append(&mut self.id.to_be_bytes().to_vec());
        packet.append(&mut [Self::ACK()].to_vec());
        packet.append(&mut [self.chksum(&packet)].to_vec());
        packet
    }

    pub fn gen_nack(&self) -> Vec<u8> {
        let mut packet: Vec<u8> = Vec::new();

        packet.append(&mut self.id.to_be_bytes().to_vec());
        packet.append(&mut [Self::NACK()].to_vec());
        packet.append(&mut [self.chksum(&packet)].to_vec());
        packet
    }

    fn chksum(&self, msg: &Vec<u8>) -> u8 {
        let mut chksum: u8 = 0;
        for c in msg.iter() {
            chksum ^= c;
        }

        chksum
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
