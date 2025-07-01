# Lecture 08: Imperative commands for Deployments, Services and Troubleshooting 

---

## **Table of Contents**  
- [Why Are Imperative Commands Important?](#why-are-imperative-commands-important)  
- [Imperative Commands for Backend Deployment and Service](#imperative-commands-for-backend-deployment-and-service)  
- [Imperative Commands for Frontend Deployment and Service](#imperative-commands-for-frontend-deployment-and-service)  
- [Creating Test Pods Imperatively](#creating-test-pods-imperatively)  
- [Key Takeaways](#key-takeaways) 

---

## **Why Are Imperative Commands Important?**  

Imperative commands are crucial for:  
- **Daily Troubleshooting:** Quickly create test pods or services to check **connectivity** or **network policies**.  
- **CKA Exam:** Saves time when you need to **quickly generate YAML manifests** using `-o yaml > file.yaml`.  
- **Real-World Scenarios:** Useful when testing **accessibility**, **deploying temporary resources**, or **verifying configurations**.  

### **Important Flags to Know:**  
- **`--dry-run=client`**: **Validates** the command **locally** without contacting the **API server**. No resources are created.  
- **`--dry-run=server`**: **Validates** the command **against the API server**, ensuring **schema and admission control checks** are performed.  
- **`--rm`**: Deletes the **pod** as soon as you **exit the container**, ideal for **temporary pods** used in **troubleshooting**.  

---

## **Imperative Commands for Backend Deployment and Service**  

We'll create the **backend deployment** and **service** using **imperative commands**.  

### **Step 1: Create Backend Deployment**  

```sh
kubectl create deployment backend-deploy \
  --image=hashicorp/http-echo \
  --replicas=3 \
  --port=5678 \
  --dry-run=client -o yaml > backend-deploy.yaml
```

- **`--image`**: Specifies the **container image** (`hashicorp/http-echo`).  
- **`--replicas`**: Defines **3 replicas** for **high availability**.  
- **`--port`**: The **port on which the container listens** (**5678**).  
- **`--dry-run=client`**: Validates and **outputs the manifest** (because of the `-o yaml` part) to **backend-deploy.yaml**.  

---

### **Step 2: Create Backend Service**  

```sh
kubectl expose deployment backend-deploy \
  --type=ClusterIP \
  --port=9090 \
  --target-port=5678 \
  --name=backend-svc \
  --dry-run=client -o yaml >> backend-deploy.yaml
```

- **`--type=ClusterIP`**: Creates an **internal-only service**.  
- **`--port`**: Exposes **port 9090** on the **service**.  
- **`--target-port`**: Redirects traffic to **port 5678** on the **container**.  
- **`>>`**: **Appends** the service **YAML** to **backend-deploy.yaml**.  

---

### **Manual Steps:**  

- Add the **YAML separator** (`---`) to **separate the deployment and service objects**.  
- Edit the labels as needed.
- `args` field to set the response text ("Hello from Backend").

  ```
  args:
    - "-text=Hello from Backend"
  ```

---

## **Imperative Commands for Frontend Deployment and Service**  

Next, we'll create the **frontend deployment** and **service** imperatively.  

### **Step 1: Create Frontend Deployment**  

```sh
kubectl create deployment frontend-deploy \
  --image=nginx \
  --replicas=3 \
  --port=80 \
  --dry-run=client -o yaml > frontend-deploy.yaml
```

- **`nginx`** container runs on **port 80**.  
- Saves the **YAML output** to **frontend-deploy.yaml**.  

---

### **Step 2: Create Frontend Service**  

```sh
kubectl expose deployment frontend-deploy \
  --type=NodePort \
  --port=80 \
  --target-port=80 \
  --name=frontend-svc \
  --dry-run=client -o yaml >> frontend-deploy.yaml
```

- **`--type=NodePort`**: Allows **external access** to the **frontend application**.  
- **Manual Edit Required:** You **cannot specify `--node-port=31000`** imperatively.  

---

### **Manual Steps:**  

- Edit the **service manifest** to **manually add the `nodePort` field**:  

  ```yaml
  nodePort: 31000
  ---
  ```
- Add the **YAML separator** (`---`) to **separate the deployment and service objects**.  
- Edit the labels as needed.

---

## **Labels: What You Need to Know**  

- When creating **deployments imperatively**, you **cannot add labels to pods directly**.  
- You **can add labels to pods** when creating them **imperatively**, but **deployments manage pod lifecycles**, and **adding labels to pods via deployment** is **not possible** imperatively.  

To **create an nginx pod** with **multiple labels** (`app=nginx` and `env=production`), you can use the **imperative command**:  

```sh
kubectl run nginx-pod \
  --image=nginx \
  --restart=Never \
  --labels="app=nginx,env=production"
```



- **`nginx-pod`**: The **name** of the pod.  
- **`--image=nginx`**: Specifies the **container image** to use.  
- **`--restart=Never`**: Instructs Kubernetes to **not** restart the pod automatically if it fails. 
- **`--labels="app=nginx,env=production"`**: Adds **multiple labels** to the **pod** in a **comma-separated key=value format**.  

### **Verify Labels:**  

```sh
kubectl get pods --show-labels
```


---

## **Creating Test Pods Imperatively**  

### **Imperative Command to Create a Pod:**  

```sh
kubectl run my-nginx \
  --image=nginx \
  --restart=Never \
  --labels=app=test-pod \
  --dry-run=client -o yaml > test-pod.yaml
```

- **`--restart=Never`**: Instructs Kubernetes to **not** restart the pod automatically if it fails. 
- **`--labels=app=test-pod`**: Adds **labels** directly to the **pod**.  
- Saves the **pod YAML** to **test-pod.yaml**.  

---

### **Create a Temporary Pod for Troubleshooting:**  

```sh
kubectl run test-pod \
  --rm -it \
  --restart=Never \
  --labels=app=test-pod \
  --image=nginx \
  /bin/sh
```

- **`--rm`**: **Deletes the pod** as soon as you **exit the container**.  
- **`-it`**: **Interactive terminal**, allowing you to **execute commands** within the **container**.  
- **`/bin/sh`**: **Shell access** to the **container** for **testing and troubleshooting**.  

---


## **Key Takeaways:**  

- **Imperative commands** are useful for **quick testing**, **troubleshooting**, and **generating YAML manifests**.  
- Use **`--dry-run=client`** for **local validation** and **`--dry-run=server`** for **API server validation**.  
- You **cannot specify `nodePort` imperatively**—edit the **YAML manually**.  
- **Labels** cannot be added to **pods via deployments** imperatively, but can be **added directly to pods**.  
- Use **imperative commands** to **generate YAMLs quickly**, then **edit them as needed**.  

---