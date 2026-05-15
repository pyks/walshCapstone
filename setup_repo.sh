#!/bin/bash
# ============================================================
# setup_repo.sh
# Run this ONCE inside your cloned walshCapstone folder:
#   git clone https://github.com/pyks/walshCapstone.git
#   cd walshCapstone
#   bash setup_repo.sh
# ============================================================

echo "Creating project folder structure..."

mkdir -p data/raw
mkdir -p data/processed
mkdir -p notebooks
mkdir -p outputs/figures
mkdir -p outputs/models
mkdir -p reports
mkdir -p src

# Keep empty folders tracked by git
touch data/raw/.gitkeep
touch data/processed/.gitkeep
touch outputs/figures/.gitkeep
touch outputs/models/.gitkeep

echo "Folder structure created successfully!"
echo ""
echo "Next steps:"
echo "  1. Copy all your .ipynb notebooks into notebooks/"
echo "  2. Copy your scraped CSV into data/raw/"
echo "  3. Copy your interim report .docx into reports/"
echo "  4. Run: pip install -r requirements.txt"
echo "  5. Run the scraper: python src/scraper.py"
echo ""
echo "To push everything to GitHub:"
echo "  git add ."
echo '  git commit -m "Initial project structure and scraper"'
echo "  git push origin main"
