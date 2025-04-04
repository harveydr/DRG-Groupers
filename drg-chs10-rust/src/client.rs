use chrono::NaiveDate;
use reqwest::{blocking::Client, Error};
use serde::{Deserialize, Serialize};

// 使用与服务端相同的数据结构
#[derive(Debug, Clone, Copy, PartialEq, Serialize, Deserialize)]
pub enum Gender {
    Male,
    Female,
    Unknown,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Diagnosis {
    pub id: u8,
    pub icd_code: String,
    pub icd_name: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Surgery {
    pub id: u8,
    pub icd_code: String,
    pub icd_name: String,
    pub date: NaiveDate,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Patient {
    pub vid: String,
    pub gender: Gender,
    pub age: u8,
    pub admit_date: NaiveDate,
    pub total_cost: f64,
    pub birth_weight: f64,
    pub diagnosis: Vec<Diagnosis>,
    pub surgery: Vec<Surgery>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct DrgResult {
    pub vid: String,
    pub mdc_code: String,
    pub adrg_code: String,
    pub drg_code: String,
}

pub struct DrgClient {
    client: Client,
    base_url: String,
}

impl DrgClient {
    pub fn new(base_url: &str) -> Self {
        DrgClient {
            client: Client::new(),
            base_url: base_url.to_string(),
        }
    }

    // 发送单个患者数据
    pub fn send_patient(&self, patient: Patient) -> Result<DrgResult, Error> {
        let url = format!("{}/patient", self.base_url);
        let response = self.client.post(&url).json(&patient).send()?;
        let result = response.json::<DrgResult>()?;
        Ok(result)
    }

    // 发送多个患者数据
    pub fn send_patients(&self, patients: Vec<Patient>) -> Result<Vec<DrgResult>, Error> {
        let url = format!("{}/patients", self.base_url);
        let response = self.client.post(&url).json(&patients).send()?;
        let results = response.json::<Vec<DrgResult>>()?;
        Ok(results)
    }

    // 获取特定患者的DRG结果
    pub fn get_patient_result(&self, vid: &str) -> Result<DrgResult, Error> {
        let url = format!("{}/result/{}", self.base_url, vid);
        let response = self.client.get(&url).send()?;
        
        if response.status().is_success() {
            let result = response.json::<DrgResult>()?;
            Ok(result)
        } else {
            panic!("未找到患者结果: {}", response.status());
        }
    }
}

// 示例函数
pub fn run_client_example() {
    let client = DrgClient::new("http://localhost:8080");
    
    // 创建示例患者数据
    let patient = Patient {
        vid: "123456".to_string(),
        gender: Gender::Male,
        age: 45,
        admit_date: NaiveDate::from_ymd_opt(2024, 4, 2).unwrap(),
        total_cost: 12345.67,
        birth_weight: 0.0, // 非新生儿
        diagnosis: vec![
            Diagnosis {
                id: 1,
                icd_code: "I21.0".to_string(),
                icd_name: "急性前壁心肌梗死".to_string(),
            }
        ],
        surgery: vec![
            Surgery {
                id: 1,
                icd_code: "36.06".to_string(),
                icd_name: "冠状动脉支架植入术".to_string(),
                date: NaiveDate::from_ymd_opt(2024, 4, 3).unwrap(),
            }
        ],
    };
    
    // 发送单个患者数据
    match client.send_patient(patient) {
        Ok(result) => println!("单个患者分组结果: {:?}", result),
        Err(e) => eprintln!("错误: {}", e),
    }
} 