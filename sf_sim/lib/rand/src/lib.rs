use rand;
use rand::Rng;

#[derive(Debug)]
pub struct RandSwitchMetric {}

impl RandSwitchMetric {
    pub fn voltage(&mut self) -> u8 {
        rand::thread_rng().gen_range(50 as u8, 60 as u8)
    }

    pub fn temp(&mut self) -> u8 {
        rand::thread_rng().gen_range(20 as u8, 28 as u8)
    }

    pub fn between(&mut self, low: u8, high: u8) -> u8 {
        rand::thread_rng().gen_range(low, high)
    }

    pub fn rand(&mut self) -> u8 {
        rand::thread_rng().gen()
    }
}
