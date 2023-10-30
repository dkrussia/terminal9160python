echo "Unpack packages..."
tar -xzvf packages.zip packages
echo "Install packages..."
pip install -r requirements.txt --no-index --find-links .\packages\
echo "Finish..."
