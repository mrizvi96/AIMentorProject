#!/bin/bash

# AI Mentor - Download Textbooks from Google Drive
# Downloads PDF textbooks directly to course_materials directory

set -e

echo "=============================================="
echo "AI Mentor - Downloading Textbooks from Google Drive"
echo "=============================================="
echo ""

# Create course_materials directory
mkdir -p course_materials
cd course_materials

# Function to download from Google Drive
download_gdrive() {
    local file_id=$1
    local output_name=$2

    echo "Downloading: $output_name"

    # Use gdown or wget with Google Drive direct link
    if command -v gdown &> /dev/null; then
        gdown "https://drive.google.com/uc?id=${file_id}" -O "${output_name}"
    else
        # Fallback to wget with confirmation bypass
        wget --load-cookies /tmp/cookies.txt \
            "https://docs.google.com/uc?export=download&confirm=$(wget --quiet --save-cookies /tmp/cookies.txt --keep-session-cookies --no-check-certificate 'https://docs.google.com/uc?export=download&id='${file_id} -O- | sed -rn 's/.*confirm=([0-9A-Za-z_]+).*/\1\n/p')&id=${file_id}" \
            -O "${output_name}" && rm -rf /tmp/cookies.txt
    fi

    if [ $? -eq 0 ]; then
        echo "✓ Downloaded: $output_name"
        ls -lh "$output_name"
    else
        echo "✗ Failed to download: $output_name"
    fi
    echo ""
}

# Install gdown if not available (faster and more reliable for Google Drive)
if ! command -v gdown &> /dev/null; then
    echo "Installing gdown for Google Drive downloads..."
    pip install -q gdown
    echo ""
fi

echo "Starting downloads..."
echo ""

# Download all 6 PDFs
# Extract file IDs from the Google Drive URLs

download_gdrive "1DECFKmdQjbLRQpJWQUd1J6KViRIPf6ab" "textbook_1.pdf"
download_gdrive "1WVTdiVOhe7Oov2TDG3AXIg3c8HIthSac" "textbook_2.pdf"
download_gdrive "1YAqEenI_z6CyZBSEUPgO2gjAELw5bwIt" "textbook_3.pdf"
download_gdrive "1mgJSWWzcA1PnHytQVp0kt5dyXx2NzIn0" "textbook_4.pdf"
download_gdrive "1nR4Mrx8BdTAOxGL_SXk80RRb9Oy-oeiZ" "textbook_5.pdf"
download_gdrive "1sAEmzgyx63SMQCGmCuSddnzxfXrUKFZE" "textbook_6.pdf"

echo "=============================================="
echo "Download Summary"
echo "=============================================="
echo ""

# Count downloaded files
pdf_count=$(ls -1 *.pdf 2>/dev/null | wc -l)
echo "Total PDFs downloaded: $pdf_count / 6"
echo ""

# Show file sizes
echo "Downloaded files:"
ls -lh *.pdf 2>/dev/null || echo "No PDF files found"
echo ""

# Calculate total size
total_size=$(du -sh . | cut -f1)
echo "Total size: $total_size"
echo ""

if [ $pdf_count -eq 6 ]; then
    echo "✓ All textbooks downloaded successfully!"
    echo ""
    echo "Next steps:"
    echo "1. Review the files: ls -lh course_materials/"
    echo "2. Run ingestion: cd backend && source venv/bin/activate && python ingest.py"
    echo ""
else
    echo "⚠️  Warning: Only $pdf_count / 6 files downloaded"
    echo "Some downloads may have failed. Check the output above."
    echo ""
fi

cd ..
echo "=============================================="
