import hashlib


def get_file_hash(file_path: str) -> str:
    print(f"[*] SIMULATING hash calculation for: {file_path}")
    sha256_hash = hashlib.sha256()
    sha256_hash.update(file_path.encode('utf-8'))
    return sha256_hash.hexdigest()


def run_pdfid_simulation(file_path: str) -> str:
    print(f"[*] SIMULATING 'pdfid' on: {file_path}")
    return """
 PDF Header: %PDF-1.4
 obj                  10
 endobj                9
 stream                3
 endstream             3
 xref                  1
 trailer               1
 startxref             1
 /Page                 1
 /Encrypt              0
 /JS                   2
 /JavaScript           2
 /AA                   1
 /OpenAction           1
 /AcroForm             0
 /JBIG2Decode          0
 /RichMedia            0
 /Launch               1
 /EmbeddedFile         0
 /XFA                  0
 /Colors > 2^24        0
    """