# Kubernetes Ingress on Amazon EKS

---

## Table of Contents

* [Introduction](#introduction)  
* [Why Ingress?](#why-ingress)  
* [What Are We Looking For?](#what-are-we-looking-for)  
* [What Is Ingress?](#what-is-ingress)   
* [What Is an Ingress Controller?](#what-is-an-ingress-controller)  
* [Real-World Flow: How Ingress Works](#real-world-flow-how-ingress-works)  
* [Ingress Setup: Cloud-Native vs 3rd-Party Controllers](#ingress-setup-cloud-native-vs-3rd-party-controllers)  
* [Popular Ingress Controllers](#popular-ingress-controllers)  
* [Demo 1: Path-Based Routing Using Ingress on Amazon EKS](#demo-1-path-based-routing-using-ingress-on-amazon-eks)  
  * [What Are We Going to Deploy?](#what-are-we-going-to-deploy)  
  * [Cluster Configuration](#cluster-configuration)  
  * [Prerequisites](#prerequisites)  
  * [Step 1: Provision EKS Cluster](#step-1-provision-eks-cluster)  
  * [Step 2: Install AWS Load Balancer Controller](#step-2-install-aws-load-balancer-controller)  
    * [Create IAM Policy](#create-iam-policy)  
    * [Create an IAM-Backed Kubernetes Service Account](#create-an-iam-backed-kubernetes-service-account)  
    * [Install the AWS Load Balancer Controller Using Helm](#install-the-aws-load-balancer-controller-using-helm)  
  * [Step 3: Create Deployments and Services](#step-3-create-deployments-and-services)  
  * [Step 4: Creating the Ingress Resource](#step-4-creating-the-ingress-resource)  
    * [Understanding ALB Target Types in Amazon EKS](#understanding-alb-target-types-in-amazon-eks)  
    * [Understanding `IngressClass`](#understanding-ingressclass)  
  * [Step 5: End-to-End Verification](#step-5-end-to-end-verification)  
  * [Step 6: Cleanup](#step-6-cleanup)  
* [Pre-requisites](#pre-requisites)  
  * [1. Understand DNS Resolution](#1-understand-dns-resolution)  
  * [2. Watch Ingress Part 1 – Real-World Flow of Ingress](#2-watch-ingress-part-1--real-world-flow-of-ingress)  
  * [3. Watch Ingress Part 2 – Path-Based Routing on EKS](#3-watch-ingress-part-2--path-based-routing-on-eks)  
* [Demo 2: Ingress with TLS and Custom Domain Integration on Amazon EKS](#demo-2-ingress-with-tls-and-custom-domain-integration-on-amazon-eks)  
  * [Step 1: Register Domain and Request TLS Certificate](#step-1-register-domain-and-request-tls-certificate)  
  * [Step 2: Update Ingress Resource to Enable HTTPS](#step-2-update-ingress-resource-to-enable-https)  
  * [Step 3: Create a Route 53 Record](#step-3-create-a-route-53-record)  
  * [Step 4: Verification](#step-4-verification)  
  * [Step 5: Cleanup](#step-5-cleanup)  
* [Demo 3: Name-Based Routing Using ALB Ingress on EKS](#demo-3-name-based-routing-using-alb-ingress-on-eks) 
  * [Step 1: Request Certificates in ACM](#step-1-request-certificates-in-acm)  
  * [Step 2: Update Deployments and Services](#step-2-update-deployments-and-services)  
  * [Step 3: Create Ingress for Name-Based Routing](#step-3-create-ingress-for-name-based-routing)  
  * [Step 4: Route 53 Alias Records](#step-4-route-53-alias-records)  
  * [Step 5: Verification](#step-5-verification-1)  
  * [Step 6: Cleanup](#step-6-cleanup)  
* [Conclusion](#conclusion)  
* [References](#references)  

---

## Introduction

This guide provides a complete, production-ready walkthrough of Kubernetes Ingress, from core concepts to hands-on implementation on Amazon EKS. We begin by understanding the “why” behind Ingress, explore its architecture, and compare popular ingress controllers. Using the AWS Load Balancer Controller, we then work through three practical demos:

1. Path-based routing to expose multiple services via a single ALB.
2. Enabling TLS with a custom domain using AWS Certificate Manager and Route 53.
3. Name-based routing for serving multiple domains and subdomains from one ALB.

By the end of this guide, you will not only understand how Ingress works in real-world EKS deployments but also gain the skills to integrate it with DNS, certificates, and routing strategies in a production environment.

---

## Why Ingress?

Exposing applications using a `NodePort` service is suitable for dev/test but falls short in production. In real-world Kubernetes clusters, nodes frequently scale in/out, making it impractical to expose dynamic node IPs externally.

Using a `LoadBalancer` service type improves on this by provisioning a cloud-managed load balancer (like AWS ELB). However, this brings its own challenges:

* Provisions a **Layer 4 (TCP/UDP) Load Balancer**—no native support for HTTP-level (Layer 7) routing such as path- or host-based rules.
* Each service creates a **dedicated cloud load balancer**, leading to cost and manageability concerns in microservice environments.
* **TLS termination must happen in the app**, as L4 load balancers can't decrypt HTTPS traffic.

---

## What Are We Looking For?

To run production workloads effectively, we need a Kubernetes-native solution that:

* Supports **HTTP(S)-aware routing** like `/android`, `/iphone`, or `iphone.myapp.com`.
* Uses a **single cloud Load Balancer** to serve multiple applications, reducing cost and simplifying operations.
* Supports **declarative, version-controlled routing rules** that are part of your Kubernetes manifests.

This is where **Ingress** becomes essential.

---

## What Is Ingress?

Ingress is a **Kubernetes API object** that defines how external HTTP(S) traffic is routed to internal Services. It acts as a **Layer 7 router** that uses URL paths, hostnames, or TLS settings to decide how traffic should be forwarded.

Ingress enables:

* **Path-based routing** (`/android` → `android-svc`)
* **Host-based routing** (`iphone.myapp.com` → `ios-svc`)
* **TLS termination** at the edge (not in the app)
* **A single centralized entry point** for all HTTP(S) traffic

> 🧠 Note: The Ingress resource is **declarative only**. It doesn't actually route traffic—it's just a YAML spec.

An Ingress requires an **Ingress Controller** to interpret and implement the routing logic.

---

## What Is an Ingress Controller?

An **Ingress Controller** is a component running in your cluster that **monitors Ingress resources** and **translates rules into actual load balancer configurations**.

Put simply:

> Ingress defines **what should happen**, the Ingress Controller decides **how to make it happen**.

It provisions a Layer 7 **HTTP(S) Load Balancer** and configures:

* Listeners (80/443)
* Routing rules (based on Ingress paths/hosts)
* Health checks and target group management

Though the term "L7 Load Balancer" is common, technically Kubernetes only supports **HTTP and HTTPS**, so it's more precise to say **HTTP(S) Load Balancer**.

---

## Real-World Flow: How Ingress Works

![Real-World Ingress Flow](/images/49a.png)

Let’s say **Shwetangi** visits `myapp.com/iphone`. How does this external request reach the correct Kubernetes Pod inside the cluster?

Here's what happens step by step:

1. The request from the browser travels over the internet and reaches an **external Load Balancer**.
2. This Load Balancer was **provisioned by the Ingress Controller** running inside your Kubernetes cluster.

   * If you're using a **cloud-native Ingress Controller** (like AWS LBC or GKE Ingress), the controller provisions an **L7 HTTP(S) Load Balancer** on the cloud provider automatically.
   * If you're using a **3rd-party Ingress Controller** like NGINX or HAProxy (common in on-prem or hybrid setups), a **Layer 4 Load Balancer** using a `Service: LoadBalancer` gets created, which simply forwards traffic to the Ingress Controller pod.
3. The **Ingress Controller reads the Ingress resource**, which defines routing rules — for example, all requests to `/iphone` should go to `iphone-svc`.
4. Based on these rules, the controller:

   * Updates the external Load Balancer config (in cloud-native setups), or
   * Handles routing internally after receiving traffic from the L4 LB (in 3rd-party setups).
5. The request is forwarded to the matching **Kubernetes Service (`iphone-svc`)**, which then routes it to one of the associated Pods.

> 📌 Note: The **Ingress resource is not a traffic hop**. It's a **declarative object** that the controller watches to configure external or internal routing mechanisms.



---


## Ingress Setup: Cloud-Native vs 3rd-Party Controllers

**Cloud-Native (AWS Load Balancer Controller – Demo 1)**
In managed cloud setups like EKS, the controller provisions an external **L7 ALB** from your Ingress manifest. It handles **TLS termination**, **routing**, and **load balancing**—all outside the cluster—offloading the Kubernetes control plane.

**3rd-Party Controllers (NGINX, HAProxy – On-Prem or Cloud)**
These controllers run **inside the cluster** and must be exposed via a **`Service` of type `LoadBalancer`**, which provisions a **Layer 4 Load Balancer**. This forwards all traffic to the controller pod, which then:

* Handles **TLS termination**
* Applies **Ingress routing rules**
* Forwards requests to appropriate **Kubernetes Services**

All logic remains **inside the cluster**, unlike ALB-based setups.

---

## Popular Ingress Controllers

| Controller                       | Description                                                                                 |
| -------------------------------- | ------------------------------------------------------------------------------------------- |
| **AWS Load Balancer Controller** | Manages ALBs and NLBs dynamically on EKS. Deep AWS integration with high scalability        |
| **NGINX Ingress Controller**     | Most widely used, highly customizable with strong community support                         |
| **HAProxy Ingress**              | Optimized for high performance and low latency routing                                      |
| **Traefik**                      | Cloud-native, supports automatic TLS via Let’s Encrypt and real-time dynamic config updates |
| **Contour**                      | Built on Envoy, offers advanced traffic control and multi-team ingress management           |
| **Istio Ingress Gateway**        | Part of the Istio service mesh. Enables policies, mTLS, and fine-grained traffic management |

While they all support the standard Kubernetes Ingress API, their **operational models and advanced features** differ. Choose based on your **cloud, scale, and security needs**.

---

## Demo 1: Path-Based Routing Using Ingress on Amazon EKS

In this demo, we’ll deploy a lightweight multi-service application named `app1` in the namespace `app1-ns` on a **Multi-AZ Amazon EKS cluster**. This application simulates three **frontend microservices** — one for iPhone users, one for Android, and a default desktop fallback — and exposes them externally using **Kubernetes Ingress** backed by an **AWS Application Load Balancer (ALB)**.

This demo focuses on **path-based routing**, where requests are routed to different services based on the URL path. It's a production-ready pattern that enables simplified routing and centralized traffic management using native Kubernetes constructs and AWS integration.

---

### What Are We Going to Deploy?

![Alt text](/images/49c.png)

Based on the architecture diagram, here’s what the deployment involves:

1. **Three frontend microservices** under the `app1` namespace:

   * `iphone-svc` → serves requests to `/iphone`
   * `android-svc` → serves requests to `/android`
   * `desktop-svc` → serves as the default catch-all for `/` and unmatched paths

2. An **Ingress Resource** defines the routing logic, mapping URL paths to the corresponding Kubernetes Services.

3. The **AWS Load Balancer Controller (ALB Ingress Controller)** continuously watches for changes in Ingress resources and:

   * Provisions an **external HTTP(S) Load Balancer** in your AWS account
   * Creates routing rules and target groups based on the Ingress definition

4. **Traffic flow:**

   * User (e.g., Shwetangi) accesses `<lb-dnsname>/iphone` via the Internet.
   * The ALB receives the request and applies the listener rules based on path.
   * Traffic is routed directly to the corresponding Pods (on port `5678`), bypassing the NodePort layer using **target-type: ip** (enabled by the VPC CNI plugin).

5. All Kubernetes components — Services, Pods, and Ingress Controller — are deployed across **two Availability Zones**, offering fault tolerance and high availability.

> **Note:** The Ingress resource is declarative and doesn’t process traffic itself. It simply informs the Ingress Controller how the Load Balancer should be configured.

---


### Real-World Ingress Routing: `/iphone`, `/android`, and the Desktop Default

In this demo, we route traffic to different Kubernetes services based on the URL path:

* `myapp.com/iphone` routes to `iphone-svc`
* `myapp.com/android` routes to `android-svc`
* `myapp.com` (or any unmatched path) routes to `desktop-svc`

In production, end users don’t manually type these paths. Instead:

* The **Android app**, once installed from the Play Store, is hardcoded to call `myapp.com/android`, which routes to the Android service.
* The **iPhone app**, downloaded via the App Store, internally accesses `myapp.com/iphone`.
* **Desktop or browser users** who visit `myapp.com` directly are handled by a **catch-all path** in the Ingress, routing them to the `desktop-svc`.

This approach allows clean separation of traffic based on platform while keeping everything under a single domain (`myapp.com`) — handled efficiently via Ingress rules in Kubernetes.

---

### **Cluster Configuration**

![Alt text](/images/49b.png)
This demo is built on an **Amazon EKS cluster** deployed in the `us-east-2 (Ohio)` region. The cluster spans two Availability Zones: `us-east-2a` and `us-east-2b`. It includes **four worker nodes** based on `t3.small` EC2 instances.

* **Why 4 nodes?** This demo uses 4 worker nodes to showcase features like `topologySpreadConstraints`, which rely on sufficient node distribution across AZs. However, you can reduce this to 2 for basic Ingress setups.
* **Why t3.small?** This instance type is eligible under AWS’s `$100 free tier credits`, making it ideal for learning environments. When provisioning via the AWS Console, non-eligible instance types appear greyed out, simplifying selection.

---

### **Prerequisites**

#### 1. Understanding of Kubernetes Services

Before beginning, ensure you’re comfortable with Kubernetes Services. 

#### 2. Install Required Tools

Ensure the following tools are installed on your local machine or cloud jump-host:

* [AWS CLI](https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html)
* [eksctl](https://eksctl.io/installation/)
* [helm](https://helm.sh/docs/intro/install/)

---

## **Step 1: Provision EKS Cluster**

Create a file named `eks-config.yaml` with the following contents:

```yaml
apiVersion: eksctl.io/v1alpha5       # Defines the API version used by eksctl for parsing this config
kind: ClusterConfig                  # Declares the type of resource (an EKS cluster configuration)

metadata:
  name: cwvj-ingress-demo            # Name of the EKS cluster to be created
  region: us-east-2                 # AWS region where the cluster will be deployed (Ohio)
  tags:                             # Custom tags for AWS resources created as part of this cluster
    owner: varun-joshi              # Tag indicating the owner of the cluster
    bu: cwvj                        # Tag indicating business unit or project group
    project: ingress-demo           # Tag for grouping resources under the ingress demo project

availabilityZones:
  - us-east-2a                      # First availability zone for high availability
  - us-east-2b                      # Second availability zone to span the cluster

iam:
  withOIDC: true                    # Enables IAM OIDC provider, required for IAM roles for service accounts (IRSA)

managedNodeGroups:
  - name: cwvj-eks-priv-ng          # Name of the managed node group
    instanceType: t3.small          # EC2 instance type for worker nodes
    minSize: 4                      # Minimum number of nodes in the group
    maxSize: 4                      # Maximum number of nodes (fixed at 4 here; no autoscaling)
    privateNetworking: true         # Launch nodes in **private subnets only** (no public IPs)
    volumeSize: 20                  # Size (in GB) of EBS volume attached to each node
    iam:
      withAddonPolicies:           # Enables AWS-managed IAM policies for certain addons
        autoScaler: true           # Allows Cluster Autoscaler to manage this node group
        externalDNS: false         # Disables permissions for ExternalDNS (not used in this demo)
        certManager: yes           # Grants cert-manager access to manage certificates using IAM
        ebs: false                 # Disables EBS volume policy (not required here)
        fsx: false                 # Disables FSx access
        efs: false                 # Disables EFS access
        albIngress: true           # Grants permissions needed by AWS Load Balancer Controller (ALB)
        xRay: false                # Disables AWS X-Ray (tracing not needed)
        cloudWatch: false          # Disables CloudWatch logging from nodes (optional in minimal setups)
    labels:
      lifecycle: ec2-autoscaler     # Custom label applied to all nodes in this group (useful for targeting in node selectors or autoscaler configs)

```

Create the cluster using:

```bash
eksctl create cluster -f eks-config.yaml
```

Verify the node distribution across AZs:

```bash
kubectl get nodes --show-labels | grep topology.kubernetes.io/zone
```

This ensures that the nodes are evenly distributed across the specified availability zones, which is critical for demonstrating topology-aware workloads.

---

## **Step 2: Install AWS Load Balancer Controller**

The AWS Load Balancer Controller is required for managing ALBs (Application Load Balancers) in Kubernetes using the native `Ingress` API. It watches for `Ingress` resources and creates ALBs accordingly, enabling advanced HTTP features such as path-based and host-based routing. It also supports integration with target groups, health checks, SSL termination, and more.

This step involves two sub-phases:

* Setting up the IAM permissions that allow the controller to interact with AWS APIs
* Installing the controller itself using Helm

---

### **2.1 Create IAM Policy**

The AWS Load Balancer Controller requires specific IAM permissions to provision and manage ALB resources on your behalf (such as creating Target Groups, Listeners, and Rules).

Download the required IAM policy:

```bash
curl -O https://raw.githubusercontent.com/kubernetes-sigs/aws-load-balancer-controller/v2.13.3/docs/install/iam_policy.json
```

Create the policy in your AWS account:

```bash
aws iam create-policy \
  --policy-name AWSLoadBalancerControllerIAMPolicy \
  --policy-document file://iam_policy.json
```

> The created policy will be used to grant your controller the ability to call ELB, EC2, and IAM APIs. You can inspect the JSON file for exact permissions.

---

### **2.2 Create an IAM-Backed Kubernetes Service Account**

We now create a Kubernetes `ServiceAccount` that is linked to the IAM policy created above. This is achieved using `eksctl`, which automatically sets up the necessary IAM Role and CloudFormation resources under the hood.

```bash
eksctl create iamserviceaccount \
  --cluster=cwvj-ingress-demo \
  --namespace=kube-system \
  --name=aws-load-balancer-controller \
  --attach-policy-arn=arn:aws:iam::261358761470:policy/AWSLoadBalancerControllerIAMPolicy \
  --override-existing-serviceaccounts \
  --region us-east-2 \
  --approve
```

This command does the following:

* Creates an **IAM Role** with the required policy attached (visible in AWS CloudFormation).
* Annotates a Kubernetes **ServiceAccount** with this role.
* Binds the ServiceAccount to the controller pods that we will deploy in the next step.

To verify:

```bash
kubectl get sa -n kube-system aws-load-balancer-controller -o yaml
```

Example output:

```yaml
apiVersion: v1
kind: ServiceAccount
metadata:
  name: aws-load-balancer-controller
  namespace: kube-system
  annotations:
    eks.amazonaws.com/role-arn: arn:aws:iam::261358761470:role/eksctl-cwvj-ingress-demo-addon-iamserviceacco-Role1-Llblca1iSsNh
```

This annotation allows the controller pod to **assume the IAM role** and make API calls securely from within the cluster.

---

### **2.3 Install the AWS Load Balancer Controller Using Helm**

> Note: The **AWS Load Balancer Controller** was previously known as the **ALB Ingress Controller**. While the functionality has expanded beyond ALBs, many community articles and annotations still use the older term. The official and recommended name is now AWS Load Balancer Controller.

Add the AWS-maintained Helm chart repository:

```bash
helm repo add eks https://aws.github.io/eks-charts
helm repo update eks
```

Install the controller:

```bash
helm install aws-load-balancer-controller eks/aws-load-balancer-controller \
  -n kube-system \
  --set clusterName=cwvj-ingress-demo \
  --set serviceAccount.create=false \
  --set serviceAccount.name=aws-load-balancer-controller \
  --version 1.13.0
```

> The `--set serviceAccount.create=false` flag ensures that Helm does not attempt to create a new service account. We are using the one we created and annotated earlier using `eksctl`.

> `helm list` alone won’t show the AWS Load Balancer Controller, as it’s installed in the `kube-system` namespace. Use `helm list -n kube-system` or `helm list -A` to view it.


Optional: List available versions of the chart

```bash
helm search repo eks/aws-load-balancer-controller --versions
```

Verify that the controller is installed:

```bash
kubectl get deployment -n kube-system aws-load-balancer-controller
```

Expected output:

```
NAME                           READY   UP-TO-DATE   AVAILABLE   AGE
aws-load-balancer-controller   2/2     2            2           84s
```

Inspect the pods to verify the correct service account is mounted:

```bash
kubectl describe pods -n kube-system -l app.kubernetes.io/name=aws-load-balancer-controller
```

Look for this line under the pod description:

```
Service Account: aws-load-balancer-controller
```

This confirms the pods are using the IAM-bound service account, enabling them to create ALBs, target groups, and associated rules when `Ingress` resources are created.

---
**Reference Links**

* **AWS Documentation**: [Installing AWS Load Balancer Controller](https://docs.aws.amazon.com/eks/latest/userguide/lbc-helm.html)
* **GitHub Repository**: [AWS Load Balancer Controller GitHub](https://github.com/kubernetes-sigs/aws-load-balancer-controller)


---

## Step 3: Create Deployments and Services for iPhone, Android, and Desktop Users

This step creates three separate deployments and corresponding services, each exposing a static HTML page to simulate platform-specific landing pages. These applications will be accessed via context path routing using an Ingress resource in the later steps.

---

### **3.1 Create a Dedicated Namespace**

**01-ns.yaml**

```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: app1-ns
```

> We create a dedicated namespace `app1-ns` to logically isolate all resources related to this application. Namespaces help with resource scoping, management, and RBAC.

Apply the namespace:

```bash
kubectl apply -f 01-ns.yaml
```

Set it as the default for the current context to avoid specifying `-n app1-ns` repeatedly:

```bash
kubectl config set-context --current --namespace=app1-ns
```

---

### **3.2 iPhone Deployment and Service**

**02-iphone.yaml**

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: iphone-deploy
  namespace: app1-ns
spec:
  replicas: 2
  selector:
    matchLabels:
      app: iphone-page
  template:
    metadata:
      labels:
        app: iphone-page
    spec:
      topologySpreadConstraints:
      - maxSkew: 1
        topologyKey: topology.kubernetes.io/zone
        whenUnsatisfiable: ScheduleAnyway
        labelSelector:
          matchLabels:
            app: iphone-page
      containers:
      - name: python-http
        image: python:alpine
        command: ["/bin/sh", "-c"]
        args:
          - |
            mkdir -p /iphone && echo '<html>
              <head><title>iPhone Users</title></head>
              <body>
                <h1>iPhone Users</h1>
                <p>Welcome to EKS Training by Varun Joshi</p>
              </body>
            </html>' > /iphone/index.html && cd / && python3 -m http.server 5678
        ports:
        - containerPort: 5678
---
apiVersion: v1
kind: Service
metadata:
  name: iphone-svc
  namespace: app1-ns
  annotations:
    alb.ingress.kubernetes.io/healthcheck-path: /iphone/index.html
spec:
  selector:
    app: iphone-page
  ports:
  - protocol: TCP
    port: 80
    targetPort: 5678
```

**Explanation:**

* `python:alpine` image runs a minimal HTTP server on port `5678` to serve `/iphone/index.html`.
* `topologySpreadConstraints` ensure pods are distributed across availability zones (`topology.kubernetes.io/zone`) with `maxSkew: 1`, minimizing zonal skew.
* The Service listens on port 80 (ClusterIP), forwarding to container port 5678.
* ALB health check is scoped to `/iphone/index.html` via annotation on the service.

Apply the resources:

```bash
kubectl apply -f 02-iphone.yaml
```

---

### **3.3 Android Deployment and Service**

**03-android.yaml**

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: android-deploy
  namespace: app1-ns
spec:
  replicas: 2
  selector:
    matchLabels:
      app: android-page
  template:
    metadata:
      labels:
        app: android-page
    spec:
      topologySpreadConstraints:
      - maxSkew: 1
        topologyKey: topology.kubernetes.io/zone
        whenUnsatisfiable: ScheduleAnyway
        labelSelector:
          matchLabels:
            app: android-page
      containers:
      - name: python-http
        image: python:alpine
        command: ["/bin/sh", "-c"]
        args:
          - |
            mkdir -p /android && echo '<html>
              <head><title>Android Users</title></head>
              <body>
                <h1>Android Users</h1>
                <p>Welcome to EKS Training by Varun Joshi</p>
              </body>
            </html>' > /android/index.html && cd / && python3 -m http.server 5678
        ports:
        - containerPort: 5678
---
apiVersion: v1
kind: Service
metadata:
  name: android-svc
  namespace: app1-ns
  annotations:
    alb.ingress.kubernetes.io/healthcheck-path: /android/index.html
spec:
  selector:
    app: android-page
  ports:
  - protocol: TCP
    port: 80
    targetPort: 5678
```

**Explanation:**

* Follows the same pattern as iPhone, except the route is `/android/index.html`.
* Health checks are isolated per app context, which is crucial when a single ALB serves multiple routes.
* Distribution of pods across zones is maintained.

Apply the resources:

```bash
kubectl apply -f 03-android.yaml
```

---

### **3.4 Desktop Deployment and Service**

**04-desktop.yaml**

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: desktop-deploy
  namespace: app1-ns
spec:
  replicas: 2
  selector:
    matchLabels:
      app: desktop-page
  template:
    metadata:
      labels:
        app: desktop-page
    spec:
      topologySpreadConstraints:
      - maxSkew: 1
        topologyKey: topology.kubernetes.io/zone
        whenUnsatisfiable: ScheduleAnyway
        labelSelector:
          matchLabels:
            app: desktop-page
      containers:
      - name: python-http
        image: python:alpine
        command: ["/bin/sh", "-c"]
        args:
          - |
            echo '<html>
              <head><title>Desktop Users</title></head>
              <body>
                <h1>Desktop Users</h1>
                <p>Welcome to EKS Training by Varun Joshi</p>
              </body>
            </html>' > /index.html && python3 -m http.server 5678
        ports:
        - containerPort: 5678
---
apiVersion: v1
kind: Service
metadata:
  name: desktop-svc
  namespace: app1-ns
  annotations:
    alb.ingress.kubernetes.io/healthcheck-path: /index.html
spec:
  selector:
    app: desktop-page
  ports:
  - protocol: TCP
    port: 80
    targetPort: 5678
```

**Explanation:**

* Desktop variant serves content at `/index.html` from the root path, suitable for default catch-all routing.
* The rest of the configuration follows the same pattern.
* Health check path aligns with this root content.

Apply the resources:

```bash
kubectl apply -f 04-desktop.yaml
```

---

### **Verification Commands**

To verify deployments and services:

```bash
kubectl get deployments
kubectl get services
```

To verify pod distribution across AZs:

```bash
kubectl get pods -o wide --sort-by='.spec.nodeName'
```

You’ll observe that pods from each deployment are spread across both AZs, thanks to the `topologySpreadConstraints`.

---

## **Step 4: Creating the Ingress Resource**

When you apply an Ingress resource in a Kubernetes cluster configured with the **AWS Load Balancer Controller**, it acts as a blueprint. The controller watches for Ingress objects and, upon detecting this configuration, **provisions an actual AWS Application Load Balancer (ALB)** using the specifications defined in the manifest.

> Think of the Ingress resource not as a traffic hop but as a **declarative configuration** for the external ALB that will be created in AWS. The traffic still flows directly through the ALB to your service pods.

Since the AWS Load Balancer Controller is installed and mapped to a service account with the necessary IAM permissions, it can interact with AWS APIs to automatically create:

* An ALB with listeners
* Target groups for your services
* Health check settings
* Routing rules

### **Manifest: 05-ingress.yaml**

```yaml
apiVersion: networking.k8s.io/v1           # API version for Ingress resource; stable since Kubernetes v1.19
kind: Ingress                              # Declares that this manifest defines an Ingress resource
metadata:
  name: ingress-demo1                      # Name of the Ingress resource
  namespace: app1-ns                       # Namespace in which this Ingress is deployed
  annotations:
    alb.ingress.kubernetes.io/scheme: internet-facing
    # Makes the ALB internet-facing (publicly accessible); other option is 'internal' for private use

    alb.ingress.kubernetes.io/load-balancer-name: cwvj-ingress-demo1
    # Assigns a custom name to the ALB; helpful for identification in the AWS Console

    alb.ingress.kubernetes.io/target-type: ip
    # Registers individual Pod IPs (via VPC CNI) in ALB target groups, skipping NodePort/host networking

    alb.ingress.kubernetes.io/listen-ports: '[{"HTTP": 80}]'
    # Configures the ALB to listen on HTTP port 80; JSON array allows multiple listeners if needed (e.g., HTTPS)

    alb.ingress.kubernetes.io/healthcheck-protocol: HTTP
    # Defines protocol used for ALB health checks (can be HTTP or HTTPS)

    alb.ingress.kubernetes.io/healthcheck-port: traffic-port
    # Uses the same port as the listener for health checks ('traffic-port' is a special keyword)

    alb.ingress.kubernetes.io/healthcheck-interval-seconds: '15'
    # Frequency (in seconds) with which ALB sends health check requests

    alb.ingress.kubernetes.io/healthcheck-timeout-seconds: '5'
    # Max time (in seconds) to wait for a health check response

    alb.ingress.kubernetes.io/healthy-threshold-count: '2'
    # Number of successful health checks before a target is marked healthy

    alb.ingress.kubernetes.io/unhealthy-threshold-count: '2'
    # Number of failed health checks before a target is marked unhealthy

    alb.ingress.kubernetes.io/success-codes: '200'
    # ALB considers HTTP 200 as a successful health check response

spec:
  ingressClassName: alb                    # Instructs Kubernetes to use the AWS ALB Ingress Controller for this resource

  rules:                                   # List of rules that define how traffic is routed
    - http:                                # All rules here apply to HTTP traffic
        paths:                             # Each entry defines a routing path
          - path: /iphone
            pathType: Prefix               # Match all paths that start with '/iphone'
            backend:
              service:
                name: iphone-svc           # Traffic matching '/iphone' goes to this Kubernetes Service
                port:
                  number: 80               # Service port (which maps to containerPort 5678 inside pods)

          - path: /android
            pathType: Prefix               # Match all paths starting with '/android'
            backend:
              service:
                name: android-svc          # Routes traffic to android-svc
                port:
                  number: 80               # Matches the port exposed by the android-svc

          - path: /
            pathType: Prefix               # Catch-all path for requests that don't match the above
            backend:
              service:
                name: desktop-svc          # Default backend service for unmatched paths (e.g., desktop)
                port:
                  number: 80               # Service port for desktop-svc

```

Apply the resource:

```bash
kubectl apply -f 05-ingress.yaml
```

---


## Understanding ALB Target Types in Amazon EKS

When you use the **AWS Load Balancer Controller** with Kubernetes `Ingress`, the annotation `alb.ingress.kubernetes.io/target-type` controls how backend targets are registered in the ALB Target Group. It defines how traffic flows from the ALB to your Pods.

In **Demo 1**, you're performing **path-based routing** using an ALB with `/iphone`, `/android`, and `/` as prefixes. DNS, Route 53, and TLS via ACM are not introduced yet — those come in later demos.

---

### `target-type: ip` — Direct-to-Pod Routing via VPC CNI
![Alt text](/images/49d.png)
When you set `target-type: ip`, the ALB registers **Pod IPs** directly in its Target Groups. This is possible because the **AWS VPC CNI plugin** assigns each Pod a routable secondary IP from the VPC subnet range. The Kubernetes `Service` is still needed, but only for discovering the backend Pods — it does not participate in traffic forwarding.

> Reduces network hops and supports Pod-level health checks.

**Flow (Left to Right):**

```
Shwetangi → <lb-dnsname>/iphone → Internet → AWS ALB → iphone target group (type = ip) → Pod IP (via Node’s VPC ENI) → iphone container (port 5678)
```

#### Key Pointers (as per diagram):

* **Kubernetes Service** is used **only** to identify backend Pods.
* **ALB forwards traffic directly** to Pod IPs (fewer hops).
* **Requires correct Security Group rules on Node ENIs**, which are **automatically handled by the AWS Load Balancer Controller** during ALB provisioning.

Suitable for clusters using **AWS VPC CNI** (default on EKS).

---

### `target-type: instance` — NodePort-Based Routing via kube-proxy
![Alt text](/images/49e.png)
When using `target-type: instance`, the ALB registers **EC2 worker nodes** (not Pod IPs) in the Target Group. For this to work, the backing Kubernetes Service must be of type **NodePort**, which exposes a high-range port on each node. The ALB sends traffic to these NodePorts. Then, the traffic flows through **`kube-proxy`** to reach a matching Pod using internal routing.

> ⚠️ Adds more hops and only supports node-level health checks.

**Flow (Left to Right):**

```
Shwetangi → <lb-dnsname>/iphone → Internet → AWS ALB → iphone target group (type = instance) → EC2 Node (NodePort) → kube-proxy → ClusterIP Service → Pod IP → iphone container (port 5678)
```

#### Key Pointers (as per diagram):

* **ALB routes to EC2 NodePort**; traffic flows through **kube-proxy**.
* Adds **extra network hops** and indirect routing.
* **Works without VPC CNI**, making it ideal for alternate CNIs like **Calico**, **Weave**, etc.

This mode is more flexible in terms of CNI support, but slightly less efficient.

---


### **Understanding `IngressClass`**

Just like Kubernetes uses `StorageClass` to dynamically provision different types of volumes (e.g., gp3, io1), `IngressClass` enables the selection of a specific ingress controller. This is important when:

* Your cluster uses multiple ingress controllers (e.g., AWS ALB, NGINX, Istio)
* You want to default routing to a particular controller when none is explicitly mentioned

---

### When and Why You Might Run Multiple Ingress Controllers in a Cluster

##### Scenario 1: Protocol-Specific Routing

Some workloads need advanced TCP/UDP support not handled by standard ingress controllers. For instance, HAProxy may be used for Layer 4 traffic, while AWS ALB continues to serve HTTP/HTTPS apps. This allows protocol-specific handling without disrupting existing ingress flows.

##### Scenario 2: Multi-Tenant Isolation

In multi-tenant clusters, teams may need independent ingress control. One team might prefer NGINX for flexibility, while another opts for ALB due to AWS integration. Running both enables team-level autonomy without conflict.

##### Scenario 3: Environment or Regional Segmentation

Clusters shared across environments or regions often need separate ingress behavior. You might run NGINX for staging with lenient rules, and ALB for production with strict compliance. Multiple controllers help enforce such environment-specific policies cleanly.


---


Check available ingress classes:

```bash
kubectl get ingressclass
```

Sample output:

```
NAME   CONTROLLER            PARAMETERS   AGE
alb    ingress.k8s.aws/alb   <none>       3h38m
```

In our case, `alb` was auto-created during AWS LBC installation.


---
Check the deployed ingress:

```bash
kubectl get ingress
```

Sample output:

```
NAME            CLASS   HOSTS   ADDRESS                                                    PORTS   AGE
ingress-demo1   alb     *       cwvj-ingress-demo1-351634829.us-east-2.elb.amazonaws.com   80      33s
```

> **Allow up to  ~3 minutes** for the external ALB to be provisioned after applying the Ingress manifest. You can monitor its creation in the AWS Console under EC2 → Load Balancers.

---


### **Step 5: End-to-End Verification**

Before testing, let’s connect the dots by walking through the end-to-end routing flow for each path: `/iphone`, `/android`, and `/`. This will help solidify how Ingress, Services, Deployments, and AWS Load Balancer Controller work together to route external traffic to internal workloads.

---

### **Test the Routing**

Once the ALB is fully provisioned and all services report healthy targets, test routing via the ALB's DNS name.

#### **iPhone Users Route**

```
http://cwvj-ingress-demo1-351634829.us-east-2.elb.amazonaws.com/iphone
```

Expected Output:

```
iPhone Users
Welcome to EKS Training by Varun Joshi
```

This is served by the `iphone-deploy` pods, with static HTML under `/iphone/index.html`.

---

#### **Android Users Route**

```
http://cwvj-ingress-demo1-351634829.us-east-2.elb.amazonaws.com/android
```

Expected Output:

```
Android Users
Welcome to EKS Training by Varun Joshi
```

This is served by the `android-deploy` pods from `/android/index.html`.

---

#### **Desktop Users Route (Default/Catch-All)**

```
http://cwvj-ingress-demo1-351634829.us-east-2.elb.amazonaws.com/
```

Expected Output:

```
Desktop Users
Welcome to EKS Training by Varun Joshi
```

This route is matched last and acts as the catch-all fallback. If the request path doesn't match `/iphone` or `/android`, it routes to `desktop-svc`, which serves from the root (`/index.html`).

---

### **Verify the Ingress Configuration**

You can use the following command to inspect your Ingress setup and ensure everything is registered as expected:

```bash
kubectl describe ingress ingress-demo1
```

Look for:

* Ingress class (`alb`)
* Load balancer hostname (ALB DNS name)
* Path rules and associated backends
* Events showing successful sync with the AWS Load Balancer Controller

---

### **Verify from the AWS Console**

To cross-check that your Ingress configuration has been reflected properly:

Navigate to **EC2 → Load Balancers** and locate the ALB with the name defined in:

```yaml
alb.ingress.kubernetes.io/load-balancer-name: cwvj-ingress-demo1
```

Then verify:

* **Scheme** is set to `internet-facing`
* **Listener** is configured on port `80`
* **Target Groups** are created for `iphone-svc`, `android-svc`, and `desktop-svc` with target type `ip`
* **Health Check** settings for each target group match the annotations set on the respective Service
* **Routing Rules** map `/iphone`, `/android`, and `/` paths to the correct target groups


By completing this verification, you confirm that your AWS ALB was dynamically provisioned and fully configured based on the Kubernetes-native Ingress resource—bridging the gap between Kubernetes and AWS networking seamlessly.

---


### **Step 6: Cleanup**

#### **Cleanup**

To remove the Kubernetes resources created during this demo, you can run:

```bash
kubectl delete -f .
```

> This command assumes all manifest files (`Namespace`, `Deployments`, `Services`, `Ingress`) are present in the current directory and were originally applied from here.

If you prefer to delete resources manually, use:

```bash
kubectl delete ingress ingress-demo1
kubectl delete svc iphone-svc android-svc desktop-svc
kubectl delete deploy iphone-deploy android-deploy desktop-deploy
kubectl delete ns app1-ns
```

This will:

* Remove the **Ingress** and associated **AWS Application Load Balancer**
* Delete **target groups**, **listeners**, and **security groups** that were provisioned dynamically

> **Note**: If you're done with all demos and want to completely clean up your EKS environment, you can delete the entire cluster using:

```bash
eksctl delete cluster --name cwvj-ingress-demo
```

> However, since we will build upon the same cluster in **Demo 2**, do **not delete the cluster** yet.

---

## **Pre-requisites**

To fully benefit from **Part 3**, ensure you're familiar with the following concepts and prior demos:

### **1. Understand DNS Resolution**

This demo uses custom domains and TLS via ACM and Route 53. A clear understanding of DNS resolution and hosted zones is essential.

* **YouTube:** [DNS Explained](https://www.youtube.com/watch?v=hXFciOpUuOY&ab_channel=CloudWithVarJosh)
* **GitHub Notes:** [DNS Lecture Resources](https://github.com/CloudWithVarJosh/YouTube-Standalone-Lectures/tree/main/01-DNS)

---

### **2. Watch Ingress Part 1 – Real-World Flow of Ingress**

We explored **what Ingress is**, why it's important, how it works behind the scenes.

* **YouTube:** [MASTER Kubernetes Ingress | PART 1](https://www.youtube.com/watch?v=yj-ZlKTYDUI&ab_channel=CloudWithVarJosh)
* **GitHub Code:** [Day 49 Resources](https://github.com/CloudWithVarJosh/CKA-Certification-Course-2025/tree/main/Day%2049)

---

### **3. Watch Ingress Part 2 – Path-Based Routing on EKS**

We built on Part 1 with a complete hands-on demo for **path-based routing**, deploying multiple apps under a shared ALB, and understanding how routing rules are defined in Ingress manifests.

* **YouTube:** [MASTER Kubernetes Ingress | PART 2](https://www.youtube.com/watch?v=4d0dkj6Vc70&ab_channel=CloudWithVarJosh)
* **GitHub Code:** [Day 50 Resources](https://github.com/CloudWithVarJosh/CKA-Certification-Course-2025/tree/main/Day%2050)

---


## **Demo 2: Ingress with TLS and Custom Domain Integration on Amazon EKS**

In this demo, we will elevate our basic ingress setup into a more **production-ready configuration** by integrating:

* A custom domain purchased via **Route 53**
* A **TLS certificate** issued using **AWS Certificate Manager (ACM)**
* ALB configuration to accept **only HTTPS (port 443)** traffic
* **Host-based routing** support (in follow-up steps)

![Alt text](/images/51a.png)

> Note: If you're using AWS Free Tier or credits, be aware that Route 53 domain registration is a **paid** service. As an example, `.click` TLD domains typically cost around **\$3/year**, which is reasonable for your personal learning lab.

---


## **Step 1: Register Domain and Request TLS Certificate**

1. Go to the **Route 53 Console** → **Domains** → Register your domain (e.g., `cwvj.click`).
2. Once registered, Route 53 will automatically create a hosted zone with **4 name servers**.
3. Now navigate to **AWS Certificate Manager (ACM)** → **Request a certificate**.
4. Choose **"Request a public certificate"**, and enter your domain name (`cwvj.click`).
5. Choose **DNS validation**, and when prompted, allow ACM to **create the validation records** in Route 53.
6. ACM will verify the DNS ownership via CNAME records, and issue the certificate once the validation succeeds.

---

## **Step 2: Update Ingress Resource to Enable HTTPS**

Update your Ingress manifest to:

* Attach the **issued ACM certificate**
* Enable **port 443**
* Add **SSL redirection**

```yaml
# 05-ingress.yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: ingress-demo2
  namespace: app1-ns
  annotations:
    # Basic ALB configuration
    alb.ingress.kubernetes.io/scheme: internet-facing
    alb.ingress.kubernetes.io/load-balancer-name: cwvj-ingress-demo2
    alb.ingress.kubernetes.io/target-type: ip

    # ALB Listener configuration (enable both HTTP and HTTPS)
    alb.ingress.kubernetes.io/listen-ports: '[{"HTTPS":443}, {"HTTP":80}]'

    # SSL settings
    alb.ingress.kubernetes.io/certificate-arn: arn:aws:acm:us-east-2:261358761470:certificate/6ab64476-8f23-4030-a291-4e8d6a3dcb35
    alb.ingress.kubernetes.io/ssl-redirect: '443'

    # Health check parameters (inherited by each target group from service annotations)
    alb.ingress.kubernetes.io/healthcheck-protocol: HTTP
    alb.ingress.kubernetes.io/healthcheck-port: traffic-port
    alb.ingress.kubernetes.io/healthcheck-interval-seconds: '15'
    alb.ingress.kubernetes.io/healthcheck-timeout-seconds: '5'
    alb.ingress.kubernetes.io/healthy-threshold-count: '2'
    alb.ingress.kubernetes.io/unhealthy-threshold-count: '2'
    alb.ingress.kubernetes.io/success-codes: '200'

spec:
  ingressClassName: alb
  rules:
    - http:
        paths:
          - path: /iphone
            pathType: Prefix
            backend:
              service:
                name: iphone-svc
                port:
                  number: 80
          - path: /android
            pathType: Prefix
            backend:
              service:
                name: android-svc
                port:
                  number: 80
          - path: /
            pathType: Prefix
            backend:
              service:
                name: desktop-svc
                port:
                  number: 80
```

> You can now apply the manifests (assuming you’re in the `demo2/` directory):

```bash
kubectl apply -f .
```

---

### **Step 3: Create a Route 53 Record**

Once the ALB is provisioned and you have the **DNS name** from `kubectl get ingress ingress-demo2` or the **AWS Console**, you’ll need to associate your domain with this ALB.

**Instructions:**

1. Navigate to **Route 53 → Hosted Zones → cwvj.click**.
2. Click **Create Record**.
3. Since we are setting this up for the **apex domain** (`cwvj.click`), leave the **Record name** blank.
4. Select **Alias**.
5. Under “Route traffic to”, choose:

   * **Alias to: Application and Classic Load Balancer**
   * **Region: us-east-2** (or your cluster’s region)
   * **Choose Load Balancer:** Select the ALB provisioned by your Ingress (it should contain `cwvj-ingress-demo2` in the name).
6. Click **Create records**.

This will ensure that `https://cwvj.click` (and its subpaths) resolve to your newly provisioned AWS ALB.

---


## **Step 4: Verification**

Try accessing the following URLs:

```bash
https://cwvj.click/
→ Desktop Users
→ Welcome to EKS Training by Varun Joshi

https://cwvj.click/iphone/
→ iPhone Users
→ Welcome to EKS Training by Varun Joshi

https://cwvj.click/android/
→ Android Users
→ Welcome to EKS Training by Varun Joshi
```

The following behaviors should be observed:

* All HTTP requests should **automatically redirect** to HTTPS (`port 443`) as per the `ssl-redirect` annotation.
* The correct TLS certificate is served (verify in browser’s padlock → certificate → subject).
* The ALB Listener for **HTTPS (443)** should have your ACM cert attached and have routing rules derived from your Ingress paths.

You can inspect rules under:
**AWS Console → EC2 → Load Balancers → Listeners → HTTPS:443 → View/edit rules**

---

**Note on Wildcard Certificates**

If your certificate only covers `*.cwvj.click`, then the apex domain `cwvj.click` **will not be trusted** by browsers. To avoid browser warnings:

* **Reissue the cert** with both:

  * `*.cwvj.click`
  * `cwvj.click`

This ensures full coverage.

---

### **Step 5: Cleanup**

Demo 2 introduced secure access to your application using a custom domain and TLS. If you're not continuing immediately to Demo 3, here’s how to clean up what was created during this step:

#### **1. Delete Kubernetes Resources**

Run the following from the `demo2` directory:

```bash
kubectl delete -f .
```

This will delete the Ingress resource with TLS and any deployments or services defined within the same directory.

#### **2. Delete the ACM Certificate**

Navigate to **AWS Certificate Manager (ACM)** in the AWS Console and delete the **public certificate** you requested for your domain (`cwvj.click` or similar). This prevents unused certificates from lingering in your account.

#### **3. Delete the Route 53 Alias Record**

Go to **Route 53 → Hosted Zones → cwvj.click** and delete the **alias A record** that was created to point your apex domain (`cwvj.click`) to the ALB.

> ⚠️ Do **not** delete the hosted zone or domain registration if you plan to use them in **Demo 3** for host-based routing.

#### **4. Wait for ALB Auto-Cleanup (Optional)**

Once the Ingress is deleted, the **AWS Load Balancer Controller** will automatically remove the ALB provisioned for this configuration. You can monitor progress from **EC2 → Load Balancers**.

#### **5. Retain the Cluster**

The same EKS cluster (`cwvj-ingress-demo`) will be reused in **Demo 3**, where we’ll configure **name-based routing** with subdomains like `iphone.cwvj.click` and `android.cwvj.click`.

If you do not plan to proceed right away and wish to reclaim all resources, you can delete the cluster later using:

```bash
eksctl delete cluster --name cwvj-ingress-demo
```

---

## **Demo 3: Name-Based Routing Using ALB Ingress on EKS**

In this demo, we will extend our TLS-secured Ingress setup from Demo 2 and implement **host-based (name-based) routing**. This allows requests to different subdomains (e.g., `iphone.cwvj.click`, `android.cwvj.click`, `cwvj.click`) to be routed to separate services inside the Kubernetes cluster. This is a common pattern in production-grade ingress configurations where applications are hosted under different subdomains.

![Alt text](/images/51b.png)

---

## **Step 1: Request Certificates in ACM**

To enable HTTPS for multiple subdomains, we need valid TLS certificates:

1. Go to **AWS Certificate Manager (ACM)** → Request 2 public certificates:

   * One for the **apex domain**: `cwvj.click`
   * One for **wildcard subdomains**: `*.cwvj.click`

2. Choose **DNS validation** and let ACM **automatically create validation records** in Route 53.

3. Wait for ACM to validate ownership and issue the certificates. These will be used by the ALB to serve HTTPS traffic for all routes.

---

## **Step 2: Update Deployments and Services**

We modify the application deployment so that requests sent to the root (`/`) path return the desired page content directly, rather than nested under `/iphone` or `/android`.

### **Key Changes**

* The `echo` command now creates `index.html` at the root instead of under `/iphone` or `/android`.
* We update the ALB health check path to `/index.html` instead of `/android/index.html` or similar.

### **Sample Manifest for iPhone Service**

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: iphone-deploy
  namespace: app1-ns
spec:
  replicas: 2
  selector:
    matchLabels:
      app: iphone-page
  template:
    metadata:
      labels:
        app: iphone-page
    spec:
      containers:
      - name: python-http
        image: python:alpine
        command: ["/bin/sh", "-c"]
        args:
          - |
            echo '<html>
              <head><title>iPhone Users</title></head>
              <body>
                <h1>iPhone Users</h1>
                <p>Welcome to EKS Training by Varun Joshi</p>
              </body>
            </html>' > /index.html && python3 -m http.server 5678
        ports:
        - containerPort: 5678
```

```yaml
apiVersion: v1
kind: Service
metadata:
  name: iphone-svc
  namespace: app1-ns
  annotations:
    alb.ingress.kubernetes.io/healthcheck-path: /index.html
spec:
  selector:
    app: iphone-page
  ports:
  - protocol: TCP
    port: 80
    targetPort: 5678
```

Repeat similar changes for Android and Desktop services.

---

## **Step 3: Create Ingress for Name-Based Routing**

This ingress defines host-based routing and attaches both ACM certificates to the ALB.

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: ingress-demo3
  namespace: app1-ns
  annotations:
    # ALB Scheme
    alb.ingress.kubernetes.io/scheme: internet-facing
    alb.ingress.kubernetes.io/load-balancer-name: cwvj-ingress-demo3

    # Target Mode
    alb.ingress.kubernetes.io/target-type: ip
    alb.ingress.kubernetes.io/listen-ports: '[{"HTTPS":443}, {"HTTP":80}]'

    # Health Checks
    alb.ingress.kubernetes.io/healthcheck-protocol: HTTP
    alb.ingress.kubernetes.io/healthcheck-port: traffic-port
    alb.ingress.kubernetes.io/healthcheck-interval-seconds: '15'
    alb.ingress.kubernetes.io/healthcheck-timeout-seconds: '5'
    alb.ingress.kubernetes.io/healthy-threshold-count: '2'
    alb.ingress.kubernetes.io/unhealthy-threshold-count: '2'
    alb.ingress.kubernetes.io/success-codes: '200'

    # SSL
    alb.ingress.kubernetes.io/certificate-arn: arn:aws:acm:us-east-2:261358761470:certificate/6ab64476-8f23-4030-a291-4e8d6a3dcb35,arn:aws:acm:us-east-2:261358761470:certificate/c54d724c-0971-48f8-a901-ebc0e4e408af
    alb.ingress.kubernetes.io/ssl-redirect: '443'
spec:
  ingressClassName: alb
  rules:
    - host: iphone.cwvj.click
      http:
        paths:
          - path: /
            pathType: Prefix
            backend:
              service:
                name: iphone-svc
                port:
                  number: 80
    - host: android.cwvj.click
      http:
        paths:
          - path: /
            pathType: Prefix
            backend:
              service:
                name: android-svc
                port:
                  number: 80
    - host: cwvj.click
      http:
        paths:
          - path: /
            pathType: Prefix
            backend:
              service:
                name: desktop-svc
                port:
                  number: 80
```

### **Explanation**

* We add both ACM certificates: one for apex (`cwvj.click`) and one for wildcard (`*.cwvj.click`) domains.
* Each rule uses the `host` field to match subdomain requests.
* The path `/` under each host now maps to the corresponding service, thanks to our updated `index.html`.

Apply all manifests from the `demo3` directory:

```bash
kubectl apply -f .
```

---

## **Step 4: Route 53 Alias Records**

To resolve DNS:

* Create alias record: `iphone.cwvj.click` → points to ALB
* Create alias record: `android.cwvj.click` → points to ALB
* Create alias record: `cwvj.click` → points to ALB

All three subdomains should now be resolved via Route 53 and routed correctly through ALB.

> **Note:** You can **automate this entire DNS record creation** process using **[ExternalDNS](https://github.com/kubernetes-sigs/external-dns)** — a Kubernetes-native controller that dynamically manages DNS records based on your Ingress and Service resources. This demo focuses on manual setup to better understand the underlying pieces, but ExternalDNS is worth exploring for production-grade workflows.

---

## **Step 5: Verification**

Verify each of the below:

* `https://iphone.cwvj.click` → should return iPhone page
* `https://android.cwvj.click` → should return Android page
* `https://cwvj.click` → should return Desktop (catch-all) page

You can inspect listener rules in ALB to confirm host and path conditions are matching correctly.

---

## **Step 6: Cleanup**

To clean up:

1. From the `demo3` directory:

   ```bash
   kubectl delete -f .
   ```

2. In **ACM**, delete both certificates.

3. In **Route 53**, remove alias records for:

   * `iphone.cwvj.click`
   * `android.cwvj.click`
   * `cwvj.click`

4. If you’re done with the cluster:

   ```bash
   eksctl delete cluster --name cwvj-ingress-demo --region us-east-2
   ```

---

## Conclusion

Ingress is a powerful Kubernetes resource for exposing applications, and when combined with the AWS Load Balancer Controller on EKS, it enables scalable, secure, and flexible routing options. In this guide, we progressed from foundational concepts to advanced routing scenarios — implementing path-based, TLS-enabled, and name-based routing with Route 53 and ACM.

You now have a step-by-step reference for deploying, configuring, and verifying Ingress resources in a multi-AZ EKS cluster. With this knowledge, you can confidently design production-grade ingress strategies that integrate seamlessly with AWS networking and security services.

---

## References

### **Kubernetes Official Documentation**

* [Ingress Concepts](https://kubernetes.io/docs/concepts/services-networking/ingress/)
* [Ingress API Reference](https://kubernetes.io/docs/reference/generated/kubernetes-api/v1.27/#ingress-v1-networking-k8s-io)
* [IngressClass](https://kubernetes.io/docs/concepts/services-networking/ingress/#ingress-class)
* [Topology Spread Constraints](https://kubernetes.io/docs/concepts/scheduling-eviction/topology-spread-constraints/)

### **AWS Official Documentation**

* [AWS Load Balancer Controller – EKS Guide](https://docs.aws.amazon.com/eks/latest/userguide/aws-load-balancer-controller.html)
* [AWS ALB Annotations](https://kubernetes-sigs.github.io/aws-load-balancer-controller/latest/guide/ingress/annotations/)
* [Target Type in ALB](https://docs.aws.amazon.com/elasticloadbalancing/latest/application/load-balancer-targets.html#target-type)
* [AWS Certificate Manager (ACM)](https://docs.aws.amazon.com/acm/latest/userguide/acm-overview.html)
* [Amazon Route 53](https://docs.aws.amazon.com/Route53/latest/DeveloperGuide/Welcome.html)

### **AWS Load Balancer Controller Project**

* [Project GitHub (Source + Examples)](https://github.com/kubernetes-sigs/aws-load-balancer-controller)
* [Project Documentation](https://kubernetes-sigs.github.io/aws-load-balancer-controller/)

---
