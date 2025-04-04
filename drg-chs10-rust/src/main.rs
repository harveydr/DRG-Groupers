mod server;
mod client;

use std::env;
use chrono::NaiveDate;

// 定义性别枚举
#[derive(Debug, Clone, Copy, PartialEq)]
enum Gender {
    Male,
    Female,
    Unknown,
}

// 定义诊断结构体
#[derive(Debug, Clone)]
struct Diagnosis {
    id: u8,
    icd_code: String,
    icd_name: String,
}

// 定义手术结构体
#[derive(Debug, Clone)]
struct Surgery {
    id: u8,
    icd_code: String,
    icd_name: String,
}

struct Patient {
    vid: String,           // 改为 String 类型
    gender: Gender,  
    age: u8,
    admit_date: NaiveDate,  // 使用 NaiveDate 类型
    total_cost: f64, 
    birth_weight: f64,
    diagnosis: Vec<Diagnosis>,  // 使用 Vec 存储诊断列表
    surgery: Vec<Surgery>,      // 使用 Vec 存储手术列表
}

fn main() {
    let args: Vec<String> = env::args().collect();
    if args.len() > 1 {
        match args[1].as_str() {
            "server" => {
                println!("启动服务器模式");
                server::start_server().unwrap();
            }
            "client" => {
                println!("启动客户端模式");
                client::run_client_example();
            }
            _ => {
                println!("未知的命令: {}", args[1]);
                print_usage();
            }
        }
    } else {
        println!("请指定运行模式");
        print_usage();
    }
}

fn print_usage() {
    println!("使用方法:");
    println!("  cargo run server      - 启动服务器");
    println!("  cargo run client      - 运行客户端示例");
}
