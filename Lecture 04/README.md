# Lecture 4: Why & What of EKS

---

### Required CLI Tools for Working with Amazon EKS

When working with Amazon EKS (Elastic Kubernetes Service), there are **three essential CLI tools** you need to install and configure on your jumphost or local machine:

---

#### 1. AWS CLI – Connect to AWS from Your Machine

The AWS CLI is a general-purpose command line tool used to interact with nearly all AWS services, including EKS. It is essential for authentication, managing IAM, VPCs, EC2, CloudWatch, and more.

* Purpose: Connects your laptop or jumphost to AWS services.
* Installation and documentation:
  [AWS CLI Installation Guide](https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html)

---

#### 2. kubectl – The Kubernetes Command-Line Tool

`kubectl` is the standard CLI used to interact with any Kubernetes cluster, including those managed by EKS. It allows you to inspect cluster resources, deploy applications, and troubleshoot workloads.

* Purpose: Interacts directly with the Kubernetes API server.
* Installation for EKS:
  [Install kubectl for Amazon EKS](https://docs.aws.amazon.com/eks/latest/userguide/install-kubectl.html)
  [Official Kubernetes kubectl Docs](https://kubernetes.io/docs/tasks/tools/)

---

#### 3. eksctl – Lifecycle Management for EKS Clusters

`eksctl` is a purpose-built CLI tool for managing EKS clusters and associated resources. It simplifies operations like creating, updating, and deleting clusters and node groups using declarative YAML configuration. This aligns well with the workflows DevOps engineers are already familiar with through tools like Kubernetes manifests, Ansible, Terraform, and Prometheus.

* Purpose: Manages EKS clusters and node groups.
* Installation and documentation:
  [eksctl Installation Guide](https://eksctl.io/installation/)

---

### After Installation: Configure AWS CLI

Once all three CLIs are installed, you need to configure your machine to authenticate with AWS. Follow these steps:

#### Step 1: Create an Access Key

* Go to the AWS Management Console, navigate to your IAM user, and generate a new Access Key.
* You’ll receive two values: an **Access Key ID** and a **Secret Access Key**.
* Important: The Secret Access Key is shown **only once**. Store it securely (for example, in a password manager). Do not share it.

> Permissions tip: Use a user with the `AdministratorAccess` policy for this course, since we’ll be working with multiple AWS services including EKS, EC2, ELB, CloudWatch, EBS, KMS, and more.


---

#### Step 2: Configure the CLI Profile

Use your terminal to create a new AWS CLI profile named `eks-training`:

```bash
aws configure --profile eks-training
```

Example prompts:

```
AWS Access Key ID [None]: <your-access-key-id>
AWS Secret Access Key [None]: <your-secret-access-key>
Default region name [None]: us-east-1
Default output format [None]: json
```

> **Tip**: `us-east-1` is a preferred region since many new AWS features are released there first.

---

**Running Commands with a Specific Profile**

Once configured, you can run AWS CLI commands using the `--profile` flag:

```bash
aws s3 ls --profile eks-training
```

---

**Set `eks-training` as Your Default Profile**

If you'd prefer not to specify the profile every time, set it as your default profile:

**Option 1 (Temporary - for current shell session):**

```bash
export AWS_PROFILE=eks-training
```

---

**Option 2 (Permanent — Update AWS Config Files)**

To avoid passing `--profile eks-training` every time, you can configure your AWS CLI to **treat the `eks-training` profile as the default**. This allows tools like `eksctl`, `kubectl`, and `terraform` to pick it up automatically.

---

**Step 1: Update `~/.aws/config`**

Edit the AWS config file to define both the `default` and `eks-training` profiles:

```ini
[default]
region = us-east-1
output = json

[profile eks-training]
region = us-east-1
output = json
```

> With this, both profiles use the same region/output. Now let’s handle the credentials.

---

**Step 2: Update `~/.aws/credentials`**

Copy the credentials (access key and secret) from the `[eks-training]` profile to the `[default]` section as well:

```ini
[default]
aws_access_key_id = YOUR_ACCESS_KEY
aws_secret_access_key = YOUR_SECRET_KEY

[eks-training]
aws_access_key_id = YOUR_ACCESS_KEY
aws_secret_access_key = YOUR_SECRET_KEY
```

> This duplication ensures that tools looking for the `[default]` profile (which is the fallback for most AWS SDKs and CLIs) use the same credentials as your `eks-training` setup.

---

**Result**

* No need to pass `--profile eks-training` every time.
* `eksctl`, `kubectl`, `terraform`, and `aws` CLI will use the credentials and region from `[default]` automatically.
* If you switch profiles later, just update the `[default]` block accordingly.


---

### Scope of This Course

This course focuses exclusively on **Amazon EKS with Managed Node Groups**, which is the most widely used and supported configuration.

Other EKS modes and options that we will **not cover in detail** but you should be aware of include:

* **EKS with Fargate**: A serverless compute engine for containers where AWS manages node provisioning and scaling automatically.
* **EKS Hybrid Nodes**: Allows you to use on-premises or edge servers as worker nodes in an EKS cluster, with AWS managing the control plane. This provides consistent Kubernetes operations across hybrid environments without managing control plane infrastructure.
* **EKS Auto Mode**: Fully manages both the control and data planes, including compute, networking, autoscaling, and upgrades. Ideal for teams focused on application delivery, as it minimizes infrastructure overhead and includes built-in best practices for security and resilience.
* **EKS Anywhere**: Runs Kubernetes clusters on your own infrastructure (on-premises or other clouds) using the same tooling and APIs as EKS in AWS.
* **Self-Managed Node Groups**: While this course focuses on Managed Node Groups, self-managed node groups—where you manage the lifecycle of EC2 instances yourself—are an alternative you may explore separately.


---

### Why Choose Amazon EKS?

Running Kubernetes in a **self-managed setup** (using tools like `kubeadm` or `kops`) means you're responsible for managing **everything end to end**, including:

* Control plane provisioning and availability
* OS and Kubernetes patching
* Certificate rotation and security hardening
* Upgrades and version compatibility
* API server/etcd performance, scaling, and fault recovery

This approach can be acceptable for **development, learning environments, or small-scale production clusters**, but it quickly becomes **operationally intensive and risky** at scale.

Modern DevOps practices encourage teams to **focus on application delivery, reliability, and security**, rather than spending time on **undifferentiated heavy lifting** like maintaining Kubernetes internals.

With **EKS**, AWS offloads all the control plane responsibilities so teams can:

* Focus on workloads and deployment strategies
* Adopt **Infrastructure as Code (IaC)** and **GitOps** workflows confidently
* Leverage native AWS integrations (CloudWatch, IAM, VPC, ALB, RDS, etc.)
* Reduce operational overhead while maintaining high availability

However, there may still be scenarios where **self-managed Kubernetes** is preferred—for example, to support experimental features, full customization, or hybrid environments. In such cases, make sure the **control plane is highly available** across multiple availability zones and you have monitoring and backup strategies in place.

---

### What Is Amazon EKS?

**Amazon Elastic Kubernetes Service (EKS)** is a **managed Kubernetes offering** from AWS. It is an **upstream-compatible** Kubernetes distribution, meaning any Kubernetes-compliant tool, controller, or workload will work seamlessly with EKS.

![Alt text](/images/4a.png)

#### EKS Control Plane

* Managed by AWS and hosted in a **dedicated VPC**.
* Each EKS cluster has:

  * At least **2 API server nodes** (spread across 2 AZs)
  * At least **3 etcd nodes** (spread across 3 AZs)
* AWS handles:

  * Auto-healing of faulty control plane nodes
  * Patching and upgrading
  * High availability and scalability
  * Security updates and certificate rotation

You do **not pay** for the control plane nodes directly—EKS charges a flat rate per cluster.

> **Note on EKS Pricing**
> Amazon EKS is not a free service and does not offer a free tier. When you create an EKS cluster, you incur charges for both the **control plane** and the **worker nodes**. While some EC2 instance types are covered under AWS Free Tier, they are too limited in capacity for real-world Kubernetes workloads and will not be used in this course.
>
> We will take a **frugal yet efficient approach** to resource creation—keeping costs in check while ensuring you get hands-on experience with realistic EKS setups.
>
> As of now, the pricing for EKS is:
>
> * **\$0.10 per cluster per hour** for the standard Kubernetes version support.
>
> Always consult the official AWS pricing page for the most up-to-date information:
> [https://aws.amazon.com/eks/pricing/](https://aws.amazon.com/eks/pricing/)
Here's an improved version of that note:

> **Note**: Be sure to **delete your EKS cluster** once you’re done practicing to avoid unnecessary charges. You can always **recreate the cluster later** when you're ready to resume. This approach helps manage costs effectively while still allowing hands-on learning.



---

### EKS Data Plane (Worker Nodes)

The data plane consists of **EC2 instances** (or optionally **Fargate**) that run your workloads. These nodes:

* Are grouped into **node groups**, typically using an **Auto Scaling Group (ASG)**
* Can be of different types: **Managed Node Groups** (recommended) or **Self-Managed Node Groups**
* Communicate with the control plane via a secured **API server endpoint**

Each node group typically:

* Uses the same AMI and instance type
* Resides within a subnet or set of subnets (public/private)
* Scales based on demand using Auto Scaling or Kubernetes-native autoscaling tools (HPA, VPA, Cluster Autoscaler)

---

### How to Provision EKS Clusters

You have multiple options for creating and managing EKS clusters, depending on your preferred tooling and automation strategy:

#### 1. AWS Console (Manual)

* Best for beginners or quick proof-of-concept setups.
* Interactive and visual, but not repeatable or automatable.

#### 2. eksctl (Recommended for This Course)

* CLI tool purpose-built for EKS
* Supports both command-line flags and YAML-based configuration files
* Uses **AWS CloudFormation** under the hood
* Ideal for fast, repeatable cluster creation with version control
* We will use `eksctl` with a YAML config file throughout this course

#### 3. Infrastructure as Code (IaC) Tools

* **Terraform**, **Pulumi**, **AWS CDK**, or **CloudFormation**
* Provides fine-grained control and integration with CI/CD pipelines
* Essential for **GitOps workflows**, compliance, and automation at scale
* Ideal for production-grade clusters and teams managing multiple environments

---

### Creating an EKS Cluster Using `eksctl`

#### Step 1 – Create the Cluster Without a Node Group

Use the following command to create a new EKS cluster named `eks-cluster-1` in the `us-east-1` region. This command creates only the control plane—no worker nodes will be provisioned:

```bash
eksctl create cluster \
  --name eks-cluster-1 \
  --region us-east-1 \
  --zones us-east-1a,us-east-1b \
  --tags "owner=varun-joshi,bu=cis" \
  --with-oidc \
  --without-nodegroup \
```

By default, if we don’t specify the `--without-nodegroup` flag, eksctl will automatically provision **two m5.large** EC2 instances as part of a managed node group. For this demo, we want to avoid spinning up large instances unnecessarily. Instead, we’ll supply a configuration file to define the cluster setup explicitly — including instance types, desired capacity, and other settings.

> **Optional**: Add the `--dry-run` flag to preview the underlying configuration (YAML) that `eksctl` will use. This is useful if you want to customize and manage your cluster setup via a config file.
>
> ```bash
> eksctl create cluster --name eks-cluster-1 --region us-east-1 --without-nodegroup --dry-run
> ```

You can then save the output to a file for future use:

```bash
eksctl create cluster ... --dry-run > cluster-config.yaml
```

> **Tip**: Don’t hesitate to use the built-in help,`eksctl` has a well-documented and informative help system. You can explore available commands and options using:
>
> ```bash
> eksctl -h            # Top-level commands
> eksctl create -h     # Help for the 'create' subcommand
> eksctl create cluster -h  # Detailed options for cluster creation
> ```
>
> This is a great way to discover additional flags and configuration options as you gain confidence.


---

### Deleting the EKS Cluster

To delete the cluster and avoid unnecessary charges:

```bash
eksctl delete cluster --name eks-cluster-1 --region us-east-1
```

> **Important**: Always verify the cluster name and region before executing the deletion.

> **Reminder**: EKS clusters incur hourly charges even when idle. Make it a habit to delete the cluster once you're done practicing and recreate it when needed. This keeps your learning cost-effective.

---

### Key Pointers:

Amazon EKS strikes a balance between control and simplicity. It is designed to support modern Kubernetes practices like:

* Declarative infrastructure (IaC)
* GitOps-based deployment models
* Observability with integrated AWS services
* Secure and scalable multi-AZ clusters out of the box

In this course, we’ll focus on **Amazon EKS with Managed Node Groups**, the most widely adopted configuration in the industry today. We will briefly touch on:

* **Self-Managed Node Groups** for custom use cases
* Other options like **EKS on Fargate**, **EKS Anywhere**, and **EKS Blueprints** as reference points, though they are out of this course’s primary scope.

