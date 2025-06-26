# Lecture 7: EKS Cluster using Config File | K8S Deployments & Services

---

# Table of Contents

- [Deployments](#deployments)
  - [What is a Deployment?](#what-is-a-deployment)
  - [Deployment Manifest Example](#deployment-manifest-example)
- [Understanding Kubernetes Services](#understanding-kubernetes-services)
  - [Why Do We Need Services in Kubernetes?](#why-do-we-need-services-in-kubernetes)
  - [Understanding ClusterIP Service](#understanding-clusterip-service-in-kubernetes)
  - [Understanding NodePort Service](#understanding-nodeport-service-in-kubernetes)
  - [Understanding LoadBalancer Service](#understanding-loadbalancer-service-in-kubernetes)
  - [Understanding ExternalName Service](#understanding-externalname-service-in-kubernetes)
  - [Summary of Request Flow Through Each Service Type](#summary-of-the-request-flow-through-each-service-type)
- [References](#references)

---

## **Deployments**

![Alt text](/images/7a.png)

---

### **What is a Deployment?**
- Deployments build on top of ReplicaSets.
- They provide advanced features such as:
  - **Rolling updates** and rollbacks.
  - Automated updates to pods.
  - Simplified scaling and management.

---

### **Deployment Manifest Example**
```yaml
apiVersion: apps/v1  # Specifies the API version for the Deployment resource
kind: Deployment     # Declares that this YAML defines a Deployment object
metadata:
  name: nginx-deployment  # Name of the Deployment; used to identify and manage the Deployment
spec:
  replicas: 3  # Specifies the desired number of pod replicas; Kubernetes maintains this number
  selector:
    matchLabels:
      app: nginx  # Selector to find the pods this Deployment manages (must match the pod template's labels)
  template:
    metadata:
      labels:
        app: nginx  # Labels assigned to the Pods; must match the selector above
    spec:
      containers:
        - name: nginx-container  # Name of the container running inside the pod
          image: nginx  # Docker image to use for this container (defaults to 'latest' tag if none is specified)

```


### **How Deployments Build on rs**
- Deployments manage ReplicaSets and create a new version whenever updated.
- This enables **rolling updates** without downtime.

---

### Explaining Rolling Updates and Rollbacks in Deployments with Annotations

**What Are Annotations in Kubernetes?**

Annotations in Kubernetes are key-value pairs used to attach arbitrary metadata to Kubernetes objects. Unlike labels (which are used for selection and grouping), annotations are intended for non-identifying information that helps tools, scripts, or humans understand the purpose, context, or other details of the object.

#### **Key Characteristics of Annotations:**
- They do not affect the behavior of the Kubernetes object directly.
- They are primarily used for informational or operational metadata.
- They can hold small amounts of arbitrary data, such as:
  - Deployment changes  
  - Build information  
  - Links to external resources  
  - Operational notes or logs


We'll demonstrate rolling updates and rollbacks in a Kubernetes Deployment using the following steps:

---

#### **Step 1: Deployment YAML**
Here’s the initial Deployment YAML:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  annotations:
    kubernetes.io/change-cause: "Initial release with nginx 1.19"
  name: nginx-deployment
spec:
  replicas: 3
  selector:
    matchLabels:
      app: nginx
  template:
    metadata:
      labels:
        app: nginx
    spec:
      containers:
      - name: nginx-container
        image: nginx:1.19
```

- The annotation `kubernetes.io/change-cause` is added to track changes.
- This Deployment uses **nginx version 1.19**.

---

#### **Step 2: Verify the Annotation and Revision**
After applying the Deployment, verify the annotation and revision history:

```bash
kubectl rollout history deployment nginx-deployment
```

Example Output:
```
deployment.apps/nginx-deployment
REVISION  CHANGE-CAUSE
1         Initial release with nginx 1.19
```

- **Revision 1** is now annotated with the change cause provided in the YAML.

---

#### **Step 3: Upgrade to nginx 1.20**
Upgrade the nginx container to **1.20** using the following command:

```bash
kubectl set image deployment nginx-deployment nginx-container=nginx:1.20
```

**NOTE**: When you imperatively update the image for a pod managed by a **ReplicationController (rc)**, the RC does **not** perform a rolling update. Instead, it retains the existing pods, and only newly created pods will use the updated image.  
The same applies to **ReplicaSets (rs)** when used **without a Deployment**—existing pods are not replaced immediately, and only new pods will have the updated image.

Add an **annotation** to describe the change:

```bash
kubectl annotate deployments.apps nginx-deployment kubernetes.io/change-cause="Upgraded nginx 1.19 to 1.20"
```

In a production environment, you should update the **Deployment manifest** with the **change cause** and the **new image version**, then apply the updated manifest. This ensures that your configuration remains consistent, version-controlled, and follows a **declarative approach**.

Verify the rollout history to confirm the new revision and annotation:

```bash
kubectl rollout history deployment nginx-deployment
```

Example Output:
```
deployment.apps/nginx-deployment
REVISION  CHANGE-CAUSE
1         Initial release with nginx 1.19
2         Upgraded nginx 1.19 to 1.20
```

- You can also view the annotation using the command:

```bash
kubectl describe deployment nginx-deployment
```

---

#### **Step 4: Upgrade to nginx 1.21**
Further upgrade the container to **1.21**:

```bash
kubectl set image deployment nginx-deployment nginx-container=nginx:1.21
```

Annotate the deployment with the reason for this change:

```bash
kubectl annotate deployments.apps nginx-deployment kubernetes.io/change-cause="Upgraded nginx 1.20 to 1.21"
```

Verify the rollout history:

```bash
kubectl rollout history deployment nginx-deployment
```

Example Output:
```
deployment.apps/nginx-deployment
REVISION  CHANGE-CAUSE
1         Initial release with nginx 1.19
2         Upgraded nginx 1.19 to 1.20
3         Upgraded nginx 1.20 to 1.21
```

---

#### **Step 5: Perform a Rollback**

To demonstrate rollback:
1. `--to-revision` flag is required when rolling back to a specific revision. You can skip the `--to-revision` flag in case you're going to the previous revision.
2. Roll back to **nginx 1.19** (revision 1):

```bash
kubectl rollout undo deployment nginx-deployment --to-revision=1
```
**Good to know**

Every time you update a deployment (e.g., by using `kubectl set` to update the image), Kubernetes creates a new ReplicaSet in the background. The previous ReplicaSet's replica count is scaled down to `0`, and the new ReplicaSet is scaled up to the desired number of replicas. 

When you perform a rollback, Kubernetes scales down the current ReplicaSet to `0` and scales up the ReplicaSet associated with the revision you're rolling back to, effectively switching the active ReplicaSet to the previous version.

---

#### **Step 6: Verify the Rollback**
After the rollback, verify the changes:

```bash
kubectl describe deployment nginx-deployment
```

Re-check the rollout history to confirm that the Deployment is rolled back to the correct revision.

---

### Key Pointers:
1. Always annotate deployments with `kubernetes.io/change-cause` to track changes for easier management and debugging.
2. Use `kubectl rollout history` to view revision details.
3. Rollbacks can be performed to any revision using the `--to-revision` flag.

### Important Kubernetes Deployment Commands

Got it! Here's the improved one-liner list for Kubernetes Deployment commands:  

- **Create a deployment Imperatively:** `kubectl create deployment nginx-deployment --image=nginx:1.19`  
- **List all deployments:** `kubectl get deployments`  
- **Describe a deployment:** `kubectl describe deployment nginx-deployment`  
- **Update deployment image:** `kubectl set image deployment/nginx-deployment nginx-container=nginx:1.20`  
- **Scale deployment replicas:** `kubectl scale deployment/nginx-deployment --replicas=5`  
- **View rollout history:** `kubectl rollout history deployment/nginx-deployment`  
- **Annotate a deployment:** `kubectl annotate deployment nginx-deployment kubernetes.io/change-cause="Upgraded nginx 1.19 to 1.20"`  
- **Rollback to a previous revision:** `kubectl rollout undo deployment/nginx-deployment --to-revision=1` 
- **Edit a deployment:**  `kubectl edit deployment <deployment_name>`
- **Get deployment manifest in YAML format:** `kubectl get deployment <deployment_name> -o yaml`
- **Delete a deployment:** `kubectl delete deployment nginx-deployment` 

**Why `Pause` and then `Resume` a Deployment**
Pausing a deployment is useful for temporarily halting the rollout process. Key reasons include:

- **Making multiple changes**: If you need to adjust various aspects of your application, pausing lets you queue changes and apply them all at once upon resuming, avoiding multiple partial rollouts.  
- **Investigating issues**: If a problem arises during the rollout, pausing allows time to investigate and fix the issue before proceeding.  

Resuming the deployment continues the rollout from where it was paused, ensuring all pending changes are applied.

---

## Key Differences Between rc, rs, and Deployments

| Feature                | ReplicationController (rc) | ReplicaSet (rs)             | Deployment                        |
|------------------------|----------------------------|-----------------------------|-----------------------------------|
| **Selectors**          | Equality-based only        | Equality and set-based      | Equality and set-based           |
| **Updates**            | Manual                    | Manual                      | Automated (rolling updates)       |
| **Scaling**            | Manual or imperative       | Manual or imperative        | Declarative and automated         |
| **Use Case**           | Legacy workloads          | Modern workloads            | Advanced workloads with CI/CD     |

---

# **Why Do We Need Services (svc) in Kubernetes?**  

Before diving into **Kubernetes Services**, let’s first understand **why we need them** in the first place.  


## The Problem: How Do Pods Communicate?
In Kubernetes, applications run inside **pods**, and these pods are **ephemeral**—they can be created, destroyed, and rescheduled dynamically. This introduces two major challenges:  

### Challenge 1: Pod IPs Keep Changing
- Every time a pod is restarted, it gets **a new IP address**.  
- If another pod wants to communicate with it, **hardcoding the IP won’t work** since it keeps changing.  

### Challenge 2: Pods Need to Expose Their Services
- Some pods need to be **accessible from other pods within the cluster** (internal communication).  
- Some pods need to be **accessible from outside the cluster** (external communication).  
- Kubernetes doesn’t automatically handle this, so we need a way to ensure reliable **pod-to-pod and external access**.  

---
## The Solution: Kubernetes Services 
![Alt text](/images/7b.png)
A **Kubernetes Service** acts as a **stable communication endpoint** for pods. It provides:  

- **A fixed IP and DNS name** so that pods can always be found, even if their individual IPs change.  
- **Load balancing** across multiple pod replicas to distribute traffic evenly.  
- **Internal and external communication**—services allow pods to communicate **within the cluster** and expose applications **to the outside world** when needed.  

---

## Example: How Services Enable Communication in Kubernetes

Let’s say we have a **frontend application** that needs to communicate with a **backend API**. Here’s how Kubernetes Services help:  

### Step-1: User Requests the Frontend Application  
- A user visits `https://example.com`.  
- The request is received by **frontend-svc** (Frontend Service).  
- **frontend-svc** forwards the request to one of the running pods in **frontend-deploy**.  

### Step-2: Frontend Communicates with Backend
- The frontend needs data from the backend.  
- The frontend pods do **not know the backend pod IPs** because they are dynamic.  
- Instead, the frontend calls `http://backend-svc` (Backend Service).  
- **backend-svc** forwards the request to one of the backend pods running inside **backend-deploy**.  

---

## Visualizing Service-Based Communication

### Without Services (Doesn’t Work)
```
User ---> Frontend Pod (IP keeps changing) ---> Backend Pod (IP keeps changing)
```
Pods can’t reliably communicate because IPs change dynamically.

### **With Services (Works)**
```
User ---> frontend-svc ---> Frontend Pod ---> backend-svc ---> Backend Pod
```
- **frontend-svc** provides a stable entry point for the frontend.  
- **backend-svc** allows frontend pods to reliably communicate with backend pods.  


## **Key Takeways:**  
- Kubernetes **does not provide automatic communication between pods**—we need **Services** to enable **stable, reliable networking**.  
- **Services solve two main problems**:  
  - Pods have **dynamic IPs**, so services provide a **fixed IP and DNS name**.  
  - Services allow **internal communication** between pods and **external access** when needed.  
- **Example:**  
  - A **frontend-service** allows users to access the frontend.  
  - A **backend-service** ensures the frontend can communicate with backend pods.  

---

# Understanding ClusterIP Service in Kubernetes

## What is a ClusterIP Service?
A **ClusterIP** service is the default type of Kubernetes service that exposes applications **internally** within the cluster. It allows communication between different pods using an automatically assigned **internal IP address**, making it ideal for inter-service communication.

### **Analogy:**  
![Alt text](/images/7c.png)

To make understanding **Kubernetes Services** easier, we'll use an **office building complex analogy** throughout this guide. Here's how the analogy maps to Kubernetes concepts:  

| **Analogy Component**           | **Kubernetes Concept**                                      |  
|--------------------------------|-------------------------------------------------------------|  
| **Office Building Complex**     | **Kubernetes Cluster**                                      |  
| **Individual Buildings**        | **Nodes (Worker/Control Plane Nodes)**                      |  
| **Departments (HR, Finance)**   | **Pods (Running Containers)**                               |  
| **Internal Phone Extensions**   | **ClusterIP Services (Internal Communication)**             |  
 

There is an **office building complex** with **two buildings**: **Building-1** and **Building-2**. Each building has **four departments**: **HR, Finance, Security, and Technology**, with **extensions 10, 11, 12, and 13**, respectively.  

- The **HR department** can reach the **Finance department** by **dialing extension 11**, and so on.  
- This **internal phone system** only works **within the building complex**—no **external calls** are allowed.  

### **Relating to Kubernetes:**  
A **ClusterIP service** allows **pods within the cluster** to communicate with each other using **internal-only IPs**, much like using **internal extensions** within the office complex.  

```plaintext
HR (Pod) → Extension 11 (ClusterIP) → Finance (Pod)
```

### **Key Characteristics of ClusterIP Service**  
- **Internal-Only Access** – The service is accessible **only within the Kubernetes cluster** and cannot be reached from outside.  
- **Automatic DNS Resolution** – Kubernetes assigns a **stable DNS name** (e.g., `backend-svc`) that other pods can use instead of an IP address.  
- **Load Balancing Across Pods** – kube-proxy **distributes traffic** among the healthy backend pods associated with the service.  
- **Simplifies Pod Communication** – Enables seamless **service-to-service** communication without requiring pod IPs, which are dynamic and can change.  

---

## **Example: Demonstrating ClusterIP with Frontend (NGINX) and Backend (http-echo)**  

![Alt text](/images/7d.png)

### **Architecture Overview**  
We will create a **two-tier application** where:  
1. **Frontend:** Runs an NGINX container on port 80.  
2. **Backend:** Runs a simple HTTP server using the `hashicorp/http-echo` image on port 5678. This server responds with a static message.  

### **How the Frontend Communicates with the Backend**  
- The frontend pods (NGINX) will communicate with the backend using the service name **`backend-svc:9090`**.  
- **CoreDNS** resolves `backend-svc` to its ClusterIP (e.g., `10.96.26.155`).  
- The request is then forwarded to one of the backend pods by **kube-proxy**.  
- In our example the request is forwarded to the 3rd pod (`10.244.2.23:5678`)

---

## **Demo: Deploying Frontend and Backend on Kubernetes**

This demo showcases a simple two-tier application setup using:

* An NGINX-based **Frontend**
* A lightweight **HTTP Echo Backend**
* A **ClusterIP Service** for internal communication

---

### **Step 1: Deploy the Frontend (NGINX)**

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: frontend-deploy
spec:
  replicas: 3  # Run 3 frontend Pods
  selector:
    matchLabels:
      app: frontend
  template:
    metadata:
      labels:
        app: frontend
    spec:
      containers:
        - name: frontend-container
          image: nginx  # Official NGINX image
```

---

### **Step 2: Deploy the Backend (http-echo)**

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: backend-deploy
spec:
  replicas: 3  # Run 3 backend Pods
  selector:
    matchLabels:
      app: backend
  template:
    metadata:
      labels:
        app: backend
    spec:
      containers:
        - name: backend-container
          image: hashicorp/http-echo
          args:
            - "-text=Hello from Backend"  # Echo this message for every request
```

---

### **Step 3: Create Backend Service (ClusterIP)**

```yaml
apiVersion: v1
kind: Service
metadata:
  name: backend-svc
spec:
  type: ClusterIP  # Internal-only service
  ports:
    - protocol: TCP
      port: 9090  # Service port
      targetPort: 5678  # Backend pod container port
  selector:
    app: backend
```

---

### **Step 4: Verify the Setup**

Run the following commands to confirm that the frontend and backend are working correctly:

```bash
# Get deployment and pod status
kubectl get deploy,pods

# Get service information
kubectl get svc backend-svc

# Launch a temporary pod with curl installed to test internal service communication
kubectl run test-client \
  --image=nginx:alpine \
  --rm -it \
  --restart=Never \
  -- /bin/sh
```

Inside the `test-client` shell:

```sh
curl http://backend-svc:9090
# Expected output: Hello from Backend
```

> The `--rm` flag ensures the pod is **automatically deleted** after the test, keeping the environment clean.

Exit the shell with:

```sh
exit
```

---


## **Key Takeaways**

* A **ClusterIP Service** is used for **internal communication** between frontend and backend.
* **kube-proxy** handles load balancing across backend pods.
* **CoreDNS** allows services to be accessed using their DNS names (e.g., `http://backend-svc`).
* This setup illustrates the foundation of **service discovery and networking** inside Kubernetes.

---

# **Understanding NodePort Service in Kubernetes**  

## **What is a NodePort Service?**  
A **NodePort** service in Kubernetes allows **external access** to pods using a **worker node’s IP address** and a fixed port. Unlike a **ClusterIP** service, which is only accessible **inside the cluster**, a NodePort service makes applications available from **outside the cluster** using the format:  

```plaintext
http://<NodeIP>:<NodePort>
```
### **Analogy:**  

![Alt text](/images/7e.png)

To make understanding **Kubernetes Services** easier, we'll use an **office building complex analogy** throughout this guide. Here's how the analogy maps to Kubernetes concepts:  

| **Analogy Component**           | **Kubernetes Concept**                                      |  
|--------------------------------|-------------------------------------------------------------|  
| **Office Building Complex**     | **Kubernetes Cluster**                                      |  
| **Individual Buildings**        | **Nodes (Worker/Control Plane Nodes)**                      |  
| **Departments (HR, Finance)**   | **Pods (Running Containers)**                               |  
| **Internal Phone Extensions**   | **ClusterIP Services (Internal Communication)**             |  
| **Front Desk Phone Numbers**    | **NodePort Services (External Access to Nodes)**            |  


The **office building complex** still has **two buildings** with **four departments** in each: **HR, Finance, Security, and Technology** (**extensions 10, 11, 12, and 13**).  

- Each building now also has a **front-desk phone number**.  
- An **external caller** needs to have the **front desk numbers of both buildings** to ensure they can **reach any department** even if **one building is not functioning**.  
- When an external user calls the **front desk**, the **receptionist** **forwards the call** to the **correct department using internal extensions**.  

---

### **Relating to Kubernetes:**  
A **NodePort service** exposes **internal ClusterIP services** externally via a **fixed port on each worker node**. If **one node goes down**, the user must **manually switch to another node’s IP**.  


```plaintext
User → Building-1 Front Desk (NodePort) → Extension 10 (ClusterIP) → HR (Pod)

If Building-1 is down:
User → Building-2 Front Desk (NodePort) → Extension 10 (ClusterIP) → HR (Pod)
```
---
### **Key Characteristics of NodePort Service**
- **External Access** – Allows users outside the cluster to access a service using `NodeIP:NodePort`.  
- **Works Across All Nodes** – The service is available on **every worker node**, regardless of where the actual pods are running.  
- **Built on ClusterIP** – Internally, a **NodePort service forwards requests to a ClusterIP service**, which then routes traffic to the correct pod.  
- **Fixed Port Range (30000-32767)** – NodePort services use a **predefined range** to avoid conflicts with system and ephemeral ports. This range is configurable, but it’s **best practice** to keep it unchanged unless necessary.  


---

### Demo: **Exposing a Frontend Application Using a NodePort Service**

Let’s deploy a simple frontend application and expose it externally using a NodePort service.

---

### **Step 1: Frontend Deployment (`frontend.yaml`)**

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: frontend-deploy
spec:
  replicas: 3
  selector:
    matchLabels:
      app: frontend
  template:
    metadata:
      labels:
        app: frontend
    spec:
      containers:
      - name: frontend-container
        image: nginx:latest
        ports:
        - containerPort: 80
```

---

### **Step 2: NodePort Service (`frontend-service.yaml`)**

```yaml
apiVersion: v1
kind: Service
metadata:
  name: frontend-svc
spec:
  type: NodePort
  selector:
    app: frontend
  ports:
    - protocol: TCP
      port: 80
      targetPort: 80
      nodePort: 31000
```

This service exposes the application on port `31000` on all worker node IPs.

---

### **Step 3: Apply and Verify Resources**

```bash
# Apply the manifests
kubectl apply -f frontend.yaml
kubectl apply -f frontend-service.yaml

# Verify pod and service status
kubectl get pods -l app=frontend
kubectl get svc frontend-svc
```

---

### **Step 4: Test NodePort Access from Within the Cluster**

Run a temporary pod using the `busybox` image to test internal connectivity:

```bash
kubectl run test-client \
  --image=busybox:1.28 \
  --rm -it \
  --restart=Never \
  -- wget -qO- http://frontend-svc:80
```

Expected output: HTML content from the NGINX default page.

---

### **Step 5: Test External Access**

Find the public IP address of any worker node:

```bash
kubectl get nodes -o wide
```

Then access the application using curl from your local machine:

```bash
curl http://<NodeIP>:31000
```

This confirms external access to the NGINX service via NodePort.

---

## **How a NodePort Service Handles Requests (Step-by-Step Flow)**  

![Alt text](/images/7f.png)

Let’s assume:  
- A worker node has the IP **172.18.0.4**.  
- The **NodePort is 31000**.  
- The **ClusterIP assigned to `frontend-svc` is `10.96.45.120`**.  
- A **frontend pod (`frontend-pod3`) has the IP `10.244.2.10`**.  

### **Request Flow:**
1. **User accesses the frontend service using**:  
   ```plaintext
   http://172.18.0.4:31000
   ```
2. The NodePort service (`frontend-svc`) listens on all worker nodes and forwards the request to its ClusterIP (`10.96.45.120:80`).  
3. The ClusterIP service load balances the request and forwards it to a running frontend pod (e.g., `frontend-pod3` at `10.244.2.10:80`).  
4. The frontend pod processes the request and responds back to the user.

**Because the NodePort service is available on all worker nodes, the user could also access the frontend using any other worker node’s IP, for example:**  
```sh
curl http://172.18.0.5:31000
```

---

# **Understanding LoadBalancer Service in Kubernetes**  

### **What is a LoadBalancer Service?**  
A **LoadBalancer service** provides a **single, external IP address** to expose applications to the **internet**. It **builds on top of NodePort and ClusterIP services**, offering **automatic load balancing and failover**.  

### **Analogy:**  

![Alt text](/images/7g.png)

To make understanding **Kubernetes Services** easier, we'll use an **office building complex analogy** throughout this guide. Here's how the analogy maps to Kubernetes concepts:  

| **Analogy Component**           | **Kubernetes Concept**                                      |  
|--------------------------------|-------------------------------------------------------------|  
| **Office Building Complex**     | **Kubernetes Cluster**                                      |  
| **Individual Buildings**        | **Nodes (Worker/Control Plane Nodes)**                      |  
| **Departments (HR, Finance)**   | **Pods (Running Containers)**                               |  
| **Internal Phone Extensions**   | **ClusterIP Services (Internal Communication)**             |  
| **Front Desk Phone Numbers**    | **NodePort Services (External Access to Nodes)**            |  
| **Call Center**                 | **LoadBalancer Service (Single External IP)**               | 

A **call center** is now set up to manage external calls:  

- The **call center** has a **single, easy-to-remember phone number**.  
- When a **user wants to reach the HR department**, they **call the call center**.  
- The **call center** automatically directs the call to **any healthy building’s front desk**.  
- The **front desk receptionist** then uses the **internal extension** to connect the call to the **HR department**.  

### **Relating to Kubernetes:**  
A **LoadBalancer service** provides a **single external IP address** and **automatically distributes incoming traffic** to **any available NodePort service** in the cluster, ensuring **high availability**.  

```plaintext
User → Call Center (LoadBalancer) → Any Front Desk (NodePort) 
      → Extension 10 (ClusterIP) → HR (Pod)
```

- When you create a **LoadBalancer service**, Kubernetes requests a **public IP** from the **cloud provider** (e.g., AWS, GCP, Azure).  
- This **public IP** is linked to the **LoadBalancer**, which then **routes traffic** to a **NodePort service** within the cluster.  
- The **NodePort service** internally uses a **ClusterIP service** to **distribute traffic** to the **pods**.  

---

### **How This Works Behind the Scenes:**  

![Alt text](/images/7h.png)

```plaintext
<LoadBalancer External IP>:80 → NodePort (31000) 
                           → ClusterIP (80) → Pod (80)
```

1. **LoadBalancer Service:** Requests a **public IP** from the **cloud provider**.  
2. **NodePort Service:** Exposes the service on **port 31000** across **all worker nodes**.  
3. **ClusterIP Service:** Manages **internal communication** between **pods**.  
4. **Pods:** Handle the **request on port 80**, serving the **application**.  

**Important Note:** You typically won't see **LoadBalancer services** used directly in production, as the load balancing requirements of modern applications are often more complex. Instead, you'll usually find **Ingress Controllers** being used, as they offer advanced traffic management features like URL-based routing, SSL termination, and host-based routing. We'll explore Ingress Controllers in detail later in this course. 

---

## Demo: **Exposing Frontend Using a LoadBalancer Service on Amazon EKS**

Now that you’ve tested NodePort access, we will delete the NodePort service and expose the application using a LoadBalancer service. On Amazon EKS, this creates a **Classic Load Balancer (CLB)** by default.

---

### **Step 1: Delete Existing NodePort Service**

```bash
kubectl delete svc frontend-svc
```

This removes the previous NodePort service. The deployment and pods remain intact.

---

### **Step 2: Create LoadBalancer Service**

Apply the following YAML manifest:

```yaml
apiVersion: v1
kind: Service
metadata:
  name: frontend-svc
spec:
  type: LoadBalancer  # Triggers creation of an external AWS Classic Load Balancer
  selector:
    app: frontend
  ports:
    - protocol: TCP
      port: 80
      targetPort: 80
```

Apply it:

```bash
kubectl apply -f frontend-service.yaml
```

---

### **Step 3: Verify LoadBalancer Provisioning**

```bash
kubectl get svc frontend-svc
```

You will see an **EXTERNAL-IP** being provisioned. Initially, it will be in a `pending` state while AWS provisions the Classic Load Balancer. This can take 1–2 minutes.

Example output:

```
NAME            TYPE           CLUSTER-IP       EXTERNAL-IP      PORT(S)        AGE
frontend-svc    LoadBalancer   10.100.200.123   a1b2c3d4.elb.amazonaws.com   80:31234/TCP   20s
```

---

### **Step 4: Access the Application**

Once the `EXTERNAL-IP` field shows a DNS name:

```bash
curl http://<EXTERNAL-IP>
```

You should receive the default NGINX welcome page.

---

### **Step 5: Explore the Load Balancer in AWS Console**

Go to **EC2 > Load Balancers** in the AWS Management Console. You’ll notice:

* A **Classic Load Balancer (CLB)** with a name like `a1b2c3d4.elb.us-east-2.amazonaws.com`.
* The backend instances (your EKS worker nodes) registered behind it.
* Health checks configured for port 80.

---

### **Key Notes**

* A **LoadBalancer service** in Kubernetes on AWS spins up a **Classic Load Balancer** by default.
* This type of load balancer sends traffic directly to the worker nodes where the pods are scheduled.
* The service selects pods based on the `selector` and balances traffic across them.
* No need to open ports manually in the EC2 security group — Kubernetes configures them via the service controller.

---

### **Coming Up Later in This Course**

Later in the course, we will:

* Use **AWS Load Balancer Controller** to provision **Application Load Balancers (ALBs)**.
* Support **Host-based and Path-based routing** using **Ingress**.
* Terminate **TLS/SSL at the ALB level**.

---

# **Understanding ExternalName Service in Kubernetes**  

### **What is an ExternalName Service?**  

An **ExternalName service** is a **special type of service** that **maps an internal Kubernetes service name** to an **external DNS name**.  

- It does **not create a proxy or a ClusterIP**.  
- Instead, it **returns a CNAME record** that **redirects traffic** to an **external domain**. 

### **Analogy:**  
![Alt text](/images/7i.png)
To make understanding **Kubernetes Services** easier, we'll use an **office building complex analogy** throughout this guide. Here's how the analogy maps to Kubernetes concepts:  

| **Analogy Component**           | **Kubernetes Concept**                                      |  
|--------------------------------|-------------------------------------------------------------|  
| **Office Building Complex**     | **Kubernetes Cluster**                                      |  
| **Individual Buildings**        | **Nodes (Worker/Control Plane Nodes)**                      |  
| **Departments (HR, Finance)**   | **Pods (Running Containers)**                               |  
| **Internal Phone Extensions**   | **ClusterIP Services (Internal Communication)**             |  
| **Front Desk Phone Numbers**    | **NodePort Services (External Access to Nodes)**            |  
| **Call Center**                 | **LoadBalancer Service (Single External IP)**               |  
| **IT Support (111)**      | **ExternalName Service (Alias for External Services)**      |  

Each building has an **IT Support number**, which is **111**.  

- **Dialing 111** connects the caller **directly to an external entity** like the **IT Support**, without needing to know the **actual phone number** of the **IT department**.  

### **Relating to Kubernetes:**  
An **ExternalName service** acts as an **alias** that maps an **internal service name** to an **external DNS name**, allowing **internal pods** to **directly access external services**.  

```plaintext
User → IT Support 111 (ExternalName) → IT Support (External Service)
```

## **ExternalName Service Manifest Example**  

```yaml
apiVersion: v1
kind: Service
metadata:
  name: cka-db-svc
spec:
  type: ExternalName
  externalName: cka-db.judhtdmxwly6.us-east-1.rds.amazonaws.com # DNS name of the Amazon RDS Instance
```
---
### **Example Scenario:**  

![Alt text](/images/7j.png)

Suppose your **backend pods** need to connect to an **external database** hosted on **Amazon RDS**.  

- Instead of **hardcoding the RDS DNS name** in the application, you create an **ExternalName service** called **`cka-db-svc`**.  
- The application can now **connect to the database** using:  

```plaintext
http://cka-db-svc:3306
```

### **Why is This Useful?**  

- If the **RDS instance changes** (e.g., **new DNS name** for a **new RDS instance**), only the **ExternalName service needs to be updated**, not the **application code** or **deployment configuration**.  
- This ensures **decoupling of configuration from the application**, promoting **maintainability and flexibility**.  

## **When to Use an ExternalName Service:**  

- When you need to **connect Kubernetes workloads to external services** by **using a simple alias**.  
- Ideal for **integrating with third-party APIs**, **legacy systems**, or **external databases** like **Amazon RDS**.  

---

# **Summary of the Request Flow Through Each Service Type**  

### **ClusterIP (Internal-Only Communication)**  
```plaintext
HR (Pod) → Extension 11 (ClusterIP) → Finance (Pod)
```

### **NodePort (External Access with Manual IP Management)**  
```plaintext
User → Building-1 Front Desk (NodePort) → Extension 10 (ClusterIP) → HR (Pod)

If Building-1 is down:
User → Building-2 Front Desk (NodePort) → Extension 10 (ClusterIP) → HR (Pod)
```

### **LoadBalancer (Single Public IP with Automatic Failover)**  
```plaintext
User → Call Center (LoadBalancer) → Any Available Front Desk (NodePort) 
      → Extension 10 (ClusterIP) → HR (Pod)
```

### **ExternalName (Internal Service to External Service Mapping)**  
```plaintext
Internal Call → IT Support 111 (ExternalName) → IT Support (External Service)
```

---

## **Key Takeaways:**  

- **ClusterIP:** Allows **internal-only communication** between pods.  
- **NodePort:** Adds **external access** through a **specific port on each node's IP**, but requires **manual switching** if a **node goes down**.  
- **LoadBalancer:** Provides a **single public IP** with **automatic load balancing**, ideal for **production environments**.  
- **ExternalName:** Offers a **simple alias** to connect **internal services to external resources** using **DNS names**.  
- When using **ExternalName**, applications **connect to services using internal DNS names**, and **Kubernetes handles the external redirection**.  
- This **separates configuration from application logic**, ensuring **easier maintenance** and **flexibility**.  

---

## **References**
- [ReplicaSet](https://kubernetes.io/docs/concepts/workloads/controllers/replicaset/)
- [Deployment](https://kubernetes.io/docs/concepts/workloads/controllers/deployment/)
- [kubcectl Quick-Reference](https://kubernetes.io/docs/reference/kubectl/quick-reference/)