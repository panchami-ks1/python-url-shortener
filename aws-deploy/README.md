# 🚀 AWS ECS Fargate Deployment & CI/CD Guide

This folder contains the **AWS CloudFormation** templates to deploy the FastAPI URL Shortener service in a secure, highly scalable, and cost-effective managed architecture.

---

## 🏗️ Architecture Overview

The following diagram illustrates the deployment topology and how different components interact with each other:

```mermaid
graph TD
    subgraph ClientZone ["Client Internet"]
        Client["Client Browser/App"]
    end

    subgraph AWSCloud ["AWS Cloud"]
        subgraph VPC ["VPC (10.0.0.0/16)"]
            IGW["Internet Gateway (IGW)"]

            subgraph PublicSubnets ["Public Subnets (Internet-Facing)"]
                subgraph PubSubnet1 ["Public Subnet 1 (AZ-A)"]
                    ALB_A["ALB Node A"]
                    Fargate_A["ECS Fargate Task A<br/>(FastAPI App:8000)"]
                end
                subgraph PubSubnet2 ["Public Subnet 2 (AZ-B)"]
                    ALB_B["ALB Node B"]
                    Fargate_B["ECS Fargate Task B<br/>(FastAPI App:8000)"]
                end
            end

            subgraph PrivateSubnets ["Private Subnets (Isolated/Internal Only)"]
                subgraph PrivSubnet1 ["Private Subnet 1 (AZ-A)"]
                    RDS_Primary["RDS PostgreSQL Database<br/>(db.t3.micro:5432)"]
                end
                subgraph PrivSubnet2 ["Private Subnet 2 (AZ-B)"]
                    Redis_Node["ElastiCache Redis Cache<br/>(cache.t3.micro:6379)"]
                end
            end
        end

        ECR["Amazon ECR<br/>(Container Registry)"]
    end

    %% Client Request Flow
    Client -->|HTTP Request:80| IGW
    IGW --> ALB_A & ALB_B
    
    %% ALB to ECS Fargate Tasks routing
    ALB_A -.->|Route traffic:8000| Fargate_A
    ALB_B -.->|Route traffic:8000| Fargate_B
    
    %% Tasks communicating with Database and Cache
    Fargate_A & Fargate_B ===>|SQL Read/Write:5432| RDS_Primary
    Fargate_A & Fargate_B ===>|Cache queries:6379| Redis_Node
    
    %% ECS tasks pulling image from ECR
    Fargate_A & Fargate_B -.->|Pull Docker image| ECR

    %% Styling
    classDef public fill:#e1f5fe,stroke:#0288d1,stroke-width:2px;
    classDef private fill:#efebe9,stroke:#5d4037,stroke-width:2px;
    classDef external fill:#eceff1,stroke:#455a64,stroke-width:2px;
    
    class PubSubnet1,PubSubnet2,PublicSubnets public;
    class PrivSubnet1,PrivSubnet2,PrivateSubnets private;
    class Client,ECR,IGW,AWSCloud external;
```

### Component Details:
1. **Network Layer (`vpc.yml`):** Creates the VPC, Internet Gateway (IGW), subnets, and the **Amazon ECR** repository.
   - *Public Subnets:* Host the Application Load Balancer (ALB) and ECS Fargate tasks. Since Fargate tasks run in the public subnet, they can pull Docker images directly from ECR and fetch updates via the IGW, eliminating the need for a costly NAT Gateway (~$32/mo).
   - *Private Subnets:* Host the RDS Database and ElastiCache Redis, isolating them completely from public internet access.
2. **Database Layer (`database.yml`):** Provisions a single-AZ **RDS PostgreSQL** database and **ElastiCache Redis** cluster in the private subnets.
3. **Application Layer (`ecs-service.yml`):** Provisions the **ECS Fargate Cluster**, Task Definition, Service, and ALB. Traffic to the ECS containers is restricted at the network level to only allow inbound requests coming from the ALB.

---

## 🛠️ Step-by-Step Setup

Follow these steps to configure your AWS account and GitHub repository to enable fully automated deployments.

### Step 1: Configure GitHub Secrets

Go to your GitHub repository -> **Settings** -> **Secrets and variables** -> **Actions**, and add the following secrets:

| Secret Name | Description | Example / Recommended Value |
| :--- | :--- | :--- |
| `AWS_ACCESS_KEY_ID` | IAM User Access Key ID with deployment permissions | `AKIAIOSFODNN7EXAMPLE` |
| `AWS_SECRET_ACCESS_KEY` | IAM User Secret Access Key | `wJalrXUptFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY` |
| `AWS_REGION` | Target AWS Region | `us-east-1` |
| `DB_USERNAME` | Master username for the RDS database | `url_admin` |
| `DB_PASSWORD` | Strong password for the RDS database | *Generate a secure password* |
| `FASTAPI_SECRET_KEY` | Secret key used by FastAPI to sign JWT tokens | *Generate via:* `openssl rand -hex 32` |

### Step 2: Configure the Manual Approval Gate

The CI/CD pipeline enforces approval gates before deploying infrastructure and application changes:
1. Go to your GitHub repository -> **Settings** -> **Environments**.
2. Click **New environment** and enter the name **`dev`**.
3. Under **Deployment protection rules**, check **Required reviewers**.
4. Search for and select your GitHub account as the reviewer.
5. Click **Save protection rules**.

When you push code changes to `main`, the workflow will automatically run testing, and then **pause** for your manual approval before running `deploy-infra` (updating VPC, Database, Cache). Once approved, it will run `build-and-push` to ECR, and then **pause again** for your manual approval before running `deploy-app` (updating ECS Fargate Service).

### Step 3: Trigger the First Deployment

Simply push your code to the `main` branch of your repository:
```bash
git add .
git commit -m "feat: add cloudformation and cicd pipelines"
git push origin main
```
This triggers the `.github/workflows/deploy.yml` workflow:
1. **test** runs unit and integration tests using `pytest`.
2. **deploy-infra** (after you approve in GitHub Actions UI) provisions the VPC (with ECR) and the Database stacks.
3. **build-and-push** builds the Docker image and pushes it to ECR.
4. **deploy-app** (after you approve in GitHub Actions UI) provisions the Load Balancer and launches the ECS Fargate Service.

---

## 📊 Verification & Management

### 1. Retrieve the Service URL
Once the CloudFormation stack completes, you can find the public URL of your service:
- Go to the **AWS CloudFormation Console** -> select `dev-url-shortener-ecs` -> **Outputs** -> **ServiceUrl**.
- Alternatively, check the GitHub Actions workflow deployment summary logs for the `ServiceUrl`.

### 2. Verify API Docs
Navigate to `http://<ALB-DNS-NAME>/docs` in your browser to verify that the FastAPI swagger documentation loads.

### 3. Database Migrations
The Docker container automatically runs `alembic upgrade head` upon launch (defined in `Dockerfile`'s CMD instruction). Your database schemas are updated automatically on every rolling update without manual intervention!

---

## 🧹 Tearing Down the Stack

If you want to delete all resources to avoid charges:
1. Go to the **Amazon ECS Console** and select your cluster -> delete the services.
2. Go to the **Amazon ECR Console** and delete the images in the repository (CloudFormation cannot delete a repository if it contains images).
3. Go to the **AWS CloudFormation Console** and delete the stacks in reverse-dependency order:
   - Delete `dev-url-shortener-ecs`
   - Delete `dev-url-shortener-database`
   - Delete `dev-url-shortener-vpc`
