use actix_web::{web, App, HttpResponse, HttpServer, Responder, Result};
use chrono::NaiveDate;
use serde::{Deserialize, Serialize};
use std::sync::Mutex;
use std::collections::HashMap;

// 导入从 main.rs 移动的数据结构
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

// 定义DRG分组结果结构
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct DrgResult {
    pub vid: String,
    pub mdc_code: String,
    pub adrg_code: String,
    pub drg_code: String,
}

// 存储状态的应用程序数据结构
struct AppState {
    patients: Mutex<HashMap<String, Patient>>,
    drg_results: Mutex<HashMap<String, DrgResult>>,
}

// 处理单个患者请求
async fn process_patient(
    patient: web::Json<Patient>,
    data: web::Data<AppState>,
) -> Result<impl Responder> {
    let patient_data = patient.into_inner();
    let vid = patient_data.vid.clone();
    
    // 存储患者数据
    {
        let mut patients = data.patients.lock().unwrap();
        patients.insert(vid.clone(), patient_data);
    }
    
    // 模拟DRG分组处理
    let drg_result = DrgResult {
        vid: vid.clone(),
        mdc_code: "MDC_C".to_string(),
        adrg_code: "AG11".to_string(),
        drg_code: "AG11A".to_string(),
    };
    
    // 存储结果
    {
        let mut results = data.drg_results.lock().unwrap();
        results.insert(vid, drg_result.clone());
    }
    
    Ok(web::Json(drg_result))
}

// 批量处理患者请求
async fn process_patients(
    patients: web::Json<Vec<Patient>>,
    data: web::Data<AppState>,
) -> Result<impl Responder> {
    let patients_data = patients.into_inner();
    let mut results = Vec::new();
    
    for patient in patients_data {
        let vid = patient.vid.clone();
        
        // 存储患者数据
        {
            let mut patients_map = data.patients.lock().unwrap();
            patients_map.insert(vid.clone(), patient);
        }
        
        // 模拟DRG分组处理
        let drg_result = DrgResult {
            vid: vid.clone(),
            mdc_code: "MDC_C".to_string(),
            adrg_code: "AG11".to_string(),
            drg_code: "AG11A".to_string(),
        };
        
        // 存储结果
        {
            let mut results_map = data.drg_results.lock().unwrap();
            results_map.insert(vid, drg_result.clone());
        }
        
        results.push(drg_result);
    }
    
    Ok(web::Json(results))
}

// 获取特定患者的DRG结果
async fn get_patient_result(
    vid: web::Path<String>,
    data: web::Data<AppState>,
) -> Result<impl Responder> {
    let results = data.drg_results.lock().unwrap();
    if let Some(result) = results.get(&vid.into_inner()) {
        return Ok(HttpResponse::Ok().json(result));
    }
    Ok(HttpResponse::NotFound().body("未找到该患者的DRG分组结果"))
}

// 启动服务器
#[actix_web::main]
pub async fn start_server() -> std::io::Result<()> {
    println!("启动DRG分组服务器在 http://127.0.0.1:8080");
    
    let app_state = web::Data::new(AppState {
        patients: Mutex::new(HashMap::new()),
        drg_results: Mutex::new(HashMap::new()),
    });
    
    HttpServer::new(move || {
        App::new()
            .app_data(app_state.clone())
            .route("/patient", web::post().to(process_patient))
            .route("/patients", web::post().to(process_patients))
            .route("/result/{vid}", web::get().to(get_patient_result))
    })
    .bind("127.0.0.1:8080")?
    .run()
    .await
} 