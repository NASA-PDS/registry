# Diagram as Code for Registry

This is an attempt to use [Diagram as Code](https://diagrams.mingrammer.com/) to design an architecture diagram for NASA PDS Registry Service.

**Diagrams** tool utilizes [Graphviz](https://www.graphviz.org/) to render the diagram and lets you draw cloud system architecture in **Python Code**

**GitHub**: [Diagrams.mingrammer](https://github.com/mingrammer/diagrams/tree/master)

## Pre-requisites

- Brew (for MacOS/Linux users)
- Chocolatey (for Windows users)
- Python 3.9.0 or higher

> At the time of writing this document, Python 3.9 is the required version for everyone on PDS. Please confirm with project leads to ensure you're using the latest Python version.

## Providers

![aws provider](https://img.shields.io/badge/AWS-orange?logo=amazon-aws&color=ff9900)
![azure provider](https://img.shields.io/badge/Azure-orange?logo=microsoft-azure&color=0089d6)
![gcp provider](https://img.shields.io/badge/GCP-orange?logo=google-cloud&color=4285f4)
![ibm provider](https://img.shields.io/badge/IBM-orange?logo=ibm&color=052FAD)
![kubernetes provider](https://img.shields.io/badge/Kubernetes-orange?logo=kubernetes&color=326ce5)
![alibaba cloud provider](https://img.shields.io/badge/AlibabaCloud-orange?logo=alibaba-cloud&color=ff6a00)
![oracle cloud provider](https://img.shields.io/badge/OracleCloud-orange?logo=oracle&color=f80000)
![openstack provider](https://img.shields.io/badge/OpenStack-orange?logo=openstack&color=da1a32)
![firebase provider](https://img.shields.io/badge/Firebase-orange?logo=firebase&color=FFCA28)
![digital ocean provider](https://img.shields.io/badge/DigitalOcean-0080ff?logo=digitalocean&color=0080ff)
![elastic provider](https://img.shields.io/badge/Elastic-orange?logo=elastic&color=005571)
![outscale provider](https://img.shields.io/badge/OutScale-orange?color=5f87bf)
![on premise provider](https://img.shields.io/badge/OnPremise-orange?color=5f87bf)
![generic provider](https://img.shields.io/badge/Generic-orange?color=5f87bf)
![programming provider](https://img.shields.io/badge/Programming-orange?color=5f87bf)
![saas provider](https://img.shields.io/badge/SaaS-orange?color=5f87bf)
![c4 provider](https://img.shields.io/badge/C4-orange?color=5f87bf)

## Getting Started

1. Change directory to your Git folder (if you have one, or wherever you store your git code locally) and create a new working directory for diagrams. Example below :

    ```
    cd git/
    mkdir diagrams
    cd diagrams/
    ```

2. Install Graphviz

    MacOS \ Linux users:

    ```shell
    brew install graphviz
    ```

    Windows users :

    ```shell
    choco install graphviz
    ```

3. Install Diagrams

    ```shell
    # using pip (pip3)
    $ pip install diagrams
    ```

4. Create a new file within your diagrams directory

    ```shell
    touch diagrams.py
    ```

5. Here is a **Quick Start** example to get familiar with using Diagrams

    ```shell
    # diagram.py
    from diagrams import Diagram
    from diagrams.aws.compute import EC2
    from diagrams.aws.database import RDS
    from diagrams.aws.network import ELB

    with Diagram("Web Service", show=False):
        ELB("lb") >> EC2("web") >> RDS("userdb")
    ```

5. Running below command will generate the diagram

    ``` shell
    python diagram.py
    ```

6. There are several additional [examples](https://diagrams.mingrammer.com/docs/getting-started/examples) provided on their website that will guide you through the whole process of creating a architecture diagram from scratch using a provider of your choice.

>  NOTE: In most cases, you will likely end using multiple providers.

## Other Languages

- If you are familiar with Go, you can use [go-diagrams](https://github.com/blushft/go-diagrams) as well.
