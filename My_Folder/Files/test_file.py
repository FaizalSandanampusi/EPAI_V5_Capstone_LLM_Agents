from iloveapi import ILoveApi

# Initialize the client with your API keys
client = ILoveApi(
    public_key="project_public_984dd9fc1b113302c8f91971fdab37cf_LQAlqb2e55de71af2e9c2d4b6dd861e1b5375",
    secret_key="secret_key_de5d21a7253e067d8afaf38eb5985896_CuT157db12b4bcccb3df87360ccff948edef4",
)

# Create a task for PDF compression
task = client.create_task("compress")

# Process the PDF file
task.process_files("Rent Receipt Ammar.pdf")

# Download the compressed PDF
task.download("output.pdf")