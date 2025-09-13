## Usage

1.  Clone the repository:

    ```bash
    git clone https://github.com/edfoo/okx-reader.git
    cd okx-reader
    ```

2. Create and activate the virtual environment

    ```bash
    uv venv
    source .venv/bin/activate
    ```

3.  Install the dependencies using uv:

    ```bash
    uv pip install -e .
    ```

4. Load the environment variables.
   Create or update your .env file to look like this

   ```
   #!/bin/bash
   export OKX_API_KEY=''
   export OKX_SECRET=''
   export OKX_PASSPHRASE=''
   ```
   and run
   ```bash
   source .env
   ```

4.  Run the script:

    ```bash
    python okx_reader.py
    ```

    