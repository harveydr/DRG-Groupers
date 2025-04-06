import PyPDF2

def split_pdf(input_pdf_path, page_ranges, output_folder='results'):
    """
    该函数用于根据指定的页码范围拆分PDF文件。

    :param input_pdf_path: 输入PDF文件的路径
    :param page_ranges: 要拆分的页码范围列表，格式为 ['start1-end1', 'start2-end2', ...]
    """
    # 打开输入的PDF文件
    with open(input_pdf_path, 'rb') as file:
        pdf_reader = PyPDF2.PdfReader(file)

        for page_range in page_ranges:
            # 解析页码范围
            start, end = map(int, page_range.split('-'))

            # 检查页码范围是否有效
            if start < 1 or end > len(pdf_reader.pages):
                print(f"页码范围 {page_range} 无效。")
                continue

            pdf_writer = PyPDF2.PdfWriter()

            # 遍历指定的页码范围
            for page_num in range(start - 1, end):
                pdf_writer.add_page(pdf_reader.pages[page_num])

            # 生成输出文件名
            output_pdf_path = f"{output_folder}/{start}-{end}.pdf"

            # 将选定的页面写入输出文件
            with open(output_pdf_path, 'wb') as output_file:
                pdf_writer.write(output_file)

if __name__ == "__main__":
    input_pdf = '../DRG20.pdf'
    # page_ranges = ['1-65', '66-103','169-188','214-241','300-314','335-359','412-431','465-474','491-533','608-626','655-667','687-698','718-723','732-741','763-779','837-844','855-863','920-930','941-949','957-960','963-976','1032-1037','1055-1069','1085-1085','1086-1098']  # 拆分第1到第3页和第4到第6页
    page_ranges = ['65-1156']
    split_pdf(input_pdf, page_ranges, output_folder='./')
