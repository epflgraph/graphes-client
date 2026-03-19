<img src="assets/icon.png" alt="Project logo" height="64">

[![License](https://img.shields.io/github/license/epflgraph/graphes-client)](https://github.com/epflgraph/graphes-client/blob/master/LICENSE)
[![Latest Release on Github](https://img.shields.io/github/v/release/epflgraph/graphes-client?sort=semver)](https://github.com/epflgraph/graphes-client/releases/latest)
[![GitHub Stars](https://img.shields.io/github/stars/epflgraph/graphes-client?style=social)](https://github.com/epflgraph/graphes-client/stargazers)
[![Contributors](https://img.shields.io/github/contributors/epflgraph/graphes-client)](https://github.com/epflgraph/graphes-client/graphs/contributors)
[![Last Commit](https://img.shields.io/github/last-commit/epflgraph/graphes-client)](https://github.com/epflgraph/graphes-client/commits/master)
[![Open Issues](https://img.shields.io/github/issues/epflgraph/graphes-client)](https://github.com/epflgraph/graphes-client/issues)
[![Open PRs](https://img.shields.io/github/issues-pr/epflgraph/graphes-client)](https://github.com/epflgraph/graphes-client/pulls)

Why Graph?
==========
The *Graph Data Platform* - developed by the AI engineering team at the [EPFL Center for Digital Education](https://www.epfl.ch/education/educational-initiatives/cede/) - is an open-source alternative to proprietary research information systems like Elsevier Pure. It federates educational and institutional data into a semantically interconnected knowledge graph of people, publications, labs, startups, courses, video lectures, and other educational resources. The [GraphSearch](https://graphsearch.epfl.ch/en) application provides lightning-fast search and discovery of the knowledge graph, as well as LLM-powered [chatbot](https://graphsearch.epfl.ch/en/chatbot) interaction with the indexed resources.

**List of Graph services:**<br/>
 [Registry](https://github.com/epflgraph/graphregistry/)  |
       [AI](https://github.com/epflgraph/graphai/)        |
 [Ontology](https://github.com/epflgraph/graphontology/)  |
   [Search](https://github.com/epflgraph/graphsearch_ui/) |
     [Chat](https://github.com/epflgraph/graphchatbot/)   |
     [Dash](https://github.com/epflgraph/graphdashboard/) |
[DB client](https://github.com/epflgraph/graphdb-client/) |
 ES client

Graph ES Client
===============
*Graph ES Client* is a Python-based command-line interface (CLI) tool designed to facilitate the management and interaction with the Graph Data Platform's underlying ElasticSearch server. It provides a unified interface for performing various index operations, including configuration management, data import/export, and server administration tasks. The CLI is built using Python's `argparse` library, allowing users to execute commands in a structured and intuitive manner.

Configuration
=============
The CLI expects a `config.yaml` file (repository root format) describing server environments. Use the provided `config.example.yaml` as a template to create your own configuration.

Installation
============

### 🐳 Deploy with Docker
The Graph ES Client is available as a Docker image, which provides a convenient way to run the CLI without needing to set up a local Python environment. The image includes all necessary dependencies and can be easily updated by pulling the latest version from Docker Hub.

Steps to deploy with Docker:

1. Pull the image:
    ```bash
    docker pull epflgraph/graphes-client:latest
    ```

2. Run the CLI help:
    ```bash
    docker run --rm epflgraph/graphes-client:latest -h
    ```

3. Run with your local configuration mounted (recommended):
    ```bash
    docker run --rm \
    -v "$(pwd)/config.yaml:/app/config.yaml:ro" \
    epflgraph/graphes-client:latest test --env <env_name>
    ```

To run commands as `graphes [cmd]`, add this to your `~/.zshrc` file:
```
graphes() {
  docker run --rm \
    -v "$PWD/config.yaml:/app/config.yaml:ro" \
    epflgraph/graphes-client:latest "$@"
}
```
Then reload your shell:
```bash
source ~/.zshrc
```
Test with:
```bash
graphes test --env <env_name>
```

### 👨🏻‍💻 Local installation
For users who prefer to run the CLI directly on their local machine, follow these steps to set up a Python virtual environment and install the package:

1. Clone the repository:
   ```bash
   git clone https://github.com/epflgraph/graphes-client.git
   cd graphes-client
   ```

2. Create and activate a virtual environment:
   ```bash
   python3 -m venv .venv.graphes
   source .venv.graphes/bin/activate
   ```

3. Install the package:
   ```bash
   pip install .
   ```

4. Verify installation:
   ```bash
   graphes -h
   ```

5. To test the connection to a database environment:
    ```bash
    graphes test --env <env_name>
    ```
