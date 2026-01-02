#!/usr/bin/env python3
"""
테스트용 PDF 파일 생성 스크립트

Usage:
    python scripts/generate_test_pdfs.py
"""

import os
import sys
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from pypdf import PdfWriter, PdfReader
from pypdf.generic import DictionaryObject, NameObject, TextStringObject


def create_output_dir():
    """출력 디렉토리 생성"""
    output_dir = Path("tests/fixtures/pdf")
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir


def generate_sample_valid(output_dir: Path):
    """TC01: 정상 2페이지 PDF"""
    file_path = output_dir / "sample_valid.pdf"
    c = canvas.Canvas(str(file_path), pagesize=letter)

    # 페이지 1
    c.drawString(100, 750, "Sample PDF Document")
    c.drawString(100, 730, "Page 1 of 2")
    c.drawString(100, 700, "This is a valid PDF for testing purposes.")
    c.drawString(100, 680, "안녕하세요. 한글 테스트입니다.")
    c.showPage()

    # 페이지 2
    c.drawString(100, 750, "Page 2 of 2")
    c.drawString(100, 730, "End of document.")
    c.showPage()

    c.save()
    print(f"✓ Generated: {file_path}")


def generate_sample_5pages(output_dir: Path):
    """TC02: 5페이지 PDF"""
    file_path = output_dir / "sample_5pages.pdf"
    c = canvas.Canvas(str(file_path), pagesize=letter)

    for i in range(1, 6):
        c.drawString(100, 750, f"Page {i} of 5")
        c.drawString(100, 730, f"Content of page {i}")
        c.drawString(100, 710, f"Lorem ipsum dolor sit amet, page {i}")
        c.showPage()

    c.save()
    print(f"✓ Generated: {file_path}")


def generate_sample_10pages(output_dir: Path):
    """TC03: 10페이지 PDF"""
    file_path = output_dir / "sample_10pages.pdf"
    c = canvas.Canvas(str(file_path), pagesize=letter)

    for i in range(1, 11):
        c.drawString(100, 750, f"Page {i} of 10")
        c.drawString(100, 730, f"Lorem ipsum dolor sit amet, page {i}")
        c.drawString(100, 710, "The quick brown fox jumps over the lazy dog.")
        c.showPage()

    c.save()
    print(f"✓ Generated: {file_path}")


def generate_sample_with_empty_page(output_dir: Path):
    """TC04: 빈 페이지 포함 PDF (3페이지, 2번째 빈 페이지)"""
    file_path = output_dir / "sample_with_empty_page.pdf"
    c = canvas.Canvas(str(file_path), pagesize=letter)

    # 페이지 1
    c.drawString(100, 750, "Page 1 with content")
    c.drawString(100, 730, "This page has text")
    c.showPage()

    # 페이지 2 (빈 페이지)
    c.showPage()

    # 페이지 3
    c.drawString(100, 750, "Page 3 with content")
    c.drawString(100, 730, "This page also has text")
    c.showPage()

    c.save()
    print(f"✓ Generated: {file_path}")


def generate_sample_images_only(output_dir: Path):
    """TC06: 이미지만 있는 PDF (텍스트 없음)"""
    file_path = output_dir / "sample_images_only.pdf"
    c = canvas.Canvas(str(file_path), pagesize=letter)

    # 이미지 대신 도형 그리기 (텍스트 없음)
    c.rect(100, 600, 200, 100, fill=1)
    c.circle(300, 400, 50, fill=1)
    c.showPage()

    c.save()
    print(f"✓ Generated: {file_path}")


def generate_sample_corrupted(output_dir: Path):
    """TC07: 손상된 PDF"""
    file_path = output_dir / "sample_corrupted.pdf"

    # 잘못된 PDF 헤더로 파일 생성
    with open(file_path, "w") as f:
        f.write("This is not a valid PDF file.\n")
        f.write("%PDF-1.4\n")
        f.write("corrupted content...\n")
        f.write("%%EOF\n")

    print(f"✓ Generated: {file_path}")


def generate_sample_encrypted(output_dir: Path):
    """TC08: 암호화된 PDF"""
    # 먼저 정상 PDF 생성
    temp_file = output_dir / "temp_for_encryption.pdf"
    c = canvas.Canvas(str(temp_file), pagesize=letter)
    c.drawString(100, 750, "This PDF will be encrypted")
    c.drawString(100, 730, "Password: test123")
    c.save()

    # 암호화 적용
    file_path = output_dir / "sample_encrypted.pdf"
    reader = PdfReader(str(temp_file))
    writer = PdfWriter()

    for page in reader.pages:
        writer.add_page(page)

    # 비밀번호 설정
    writer.encrypt(user_password="test123", owner_password="owner123")

    with open(file_path, "wb") as f:
        writer.write(f)

    # 임시 파일 삭제
    temp_file.unlink()

    print(f"✓ Generated: {file_path}")


def generate_sample_malicious_js(output_dir: Path):
    """TC10: JavaScript 포함 PDF"""
    file_path = output_dir / "sample_malicious_js.pdf"

    # 정상 PDF 생성
    temp_file = output_dir / "temp_for_js.pdf"
    c = canvas.Canvas(str(temp_file), pagesize=letter)
    c.drawString(100, 750, "PDF with JavaScript")
    c.drawString(100, 730, "This PDF contains JavaScript code")
    c.save()

    # JavaScript 추가 (저수준 조작)
    reader = PdfReader(str(temp_file))
    writer = PdfWriter()

    for page in reader.pages:
        writer.add_page(page)

    # JavaScript 액션 추가 (간단한 예제)
    js_action = DictionaryObject()
    js_action.update({
        NameObject("/S"): NameObject("/JavaScript"),
        NameObject("/JS"): TextStringObject("app.alert('Test JavaScript');"),
    })

    # Catalog에 추가
    if writer._root_object.get("/OpenAction") is None:
        writer._root_object[NameObject("/OpenAction")] = js_action

    with open(file_path, "wb") as f:
        writer.write(f)

    temp_file.unlink()

    print(f"✓ Generated: {file_path}")


def print_manual_instructions():
    """대용량 PDF 수동 생성 안내"""
    print("\n⚠️  대용량 PDF 파일은 수동 생성이 필요합니다:")
    print("\n1. sample_large_49mb.pdf (49MB - 제한 내)")
    print("   - 방법: 여러 이미지를 포함한 PDF 생성")
    print("   - 또는: 기존 대용량 PDF 파일 복사")
    print("\n2. sample_large_150mb.pdf (150MB - 제한 초과)")
    print("   - 방법: 더 많은 이미지를 포함한 PDF 생성")
    print("   - 또는: 기존 대용량 PDF 파일 복사")
    print("\n위치: tests/fixtures/pdf/")


def main():
    """메인 함수"""
    print("📄 테스트용 PDF 파일 생성 중...\n")

    output_dir = create_output_dir()

    # 각 테스트 케이스별 PDF 생성
    try:
        generate_sample_valid(output_dir)
        generate_sample_5pages(output_dir)
        generate_sample_10pages(output_dir)
        generate_sample_with_empty_page(output_dir)
        generate_sample_images_only(output_dir)
        generate_sample_corrupted(output_dir)
        generate_sample_encrypted(output_dir)
        generate_sample_malicious_js(output_dir)

        print("\n✅ PDF 파일 생성 완료!")
        print(f"📁 위치: {output_dir.absolute()}")

        print_manual_instructions()

    except Exception as e:
        print(f"\n❌ 에러 발생: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
