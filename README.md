# fetchbin

FetchBin is a simple and fast way to share your command line outputs with others. Whether you're debugging, showcasing system information, or collaborating with teammates, FetchBin makes it easy to share terminal output in a clean, readable format.

Offical API: https://fetchbin.beucismis.org

## Install and Usage

```
pip install fetchbin

fetchbin share fastfetch

fetchbin share -s <command>  # Share as hidden
fetchbin delete <token>  # Delete a share
```

## Running with Docker

```
git clone https://github.com/beucismis/fetchbin
cd fetchbin/
docker build -t fetchbin .
sudo docker run -d -p 8000:8000 -v ~/data:/data --name fetchbin fetchbin
```

## Usage

Once the service is running, you can access the API at `http://localhost:8000`.

## License

`fetchbin` is distributed under the terms of the [GNU GPL](LICENSE.txt) license.
