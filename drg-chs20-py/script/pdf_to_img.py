import os
import fitz  # PyMuPDF库
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn


def pdf_to_images(pdf_path, output_folder):
    """
    将PDF文件的每一页转换为高质量的图片。

    :param pdf_path: PDF文件的路径
    :param output_folder: 输出图片的文件夹路径
    """
    try:
        # 创建输出目录
        if not os.path.exists(output_folder):
            os.makedirs(output_folder)
        pdf_document = fitz.open(pdf_path)
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        ) as progress:
            task = progress.add_task("[cyan]Converting PDF pages...", total=len(pdf_document))
            for page_number in range(len(pdf_document)):
                page = pdf_document.load_page(page_number)
                # 提高分辨率以获得高清图片
                pix = page.get_pixmap(matrix=fitz.Matrix(300 / 72, 300 / 72))
                image_path = f"{output_folder}/page_{page_number + 1}.png"
                pix.save(image_path)
                progress.update(task, advance=1)
        pdf_document.close()
    except FileNotFoundError:
        print(f"Error: The PDF file {pdf_path} was not found.")
    except Exception as e:
        print(f"An error occurred: {e}")


# 获取当前脚本所在目录
current_dir = os.path.dirname(os.path.abspath(__file__))
# 定义输出目录为当前目录下的image目录
output_folder = os.path.join(current_dir, 'image')
# 构建PDF文件的绝对路径
pdf_path = os.path.join(current_dir, 'data/DRG20.pdf')

# 调用函数进行转换
pdf_to_images(pdf_path, output_folder)