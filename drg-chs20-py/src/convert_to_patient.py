from data_classes import Patient, Diagnosis, Surgery


def get_patient(data):
    diagnosis_list = [Diagnosis(diag_id=diag["diag_id"], diag_code=diag["diag_code"], diag_name=diag["diag_name"]) for diag in data["diagnosis"]]
    surgery_list = [Surgery(oper_id=oper["oper_id"], oper_code=oper["oper_code"], oper_name=oper["oper_name"]) for oper in data["surgery"]]
    patient = Patient(
        vid=data["vid"],
        gender=data["gender"],
        age=data["age"],
        admit_date=data["admit_date"],
        dis_date=data["dis_date"],
        total_cost=data["total_cost"],
        birth_weight=data["birth_weight"],
        diagnosis=diagnosis_list,
        surgery=surgery_list
    )
    return patient
