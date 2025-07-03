# Lecture 10: Deploy Application on Amazon EKS with EBS-Backed Storage

---


### **Storage Classes & Dynamic Provisioning**
---
#### **What is a Storage Class?**

A **Storage Class** in Kubernetes is a way to define different storage configurations, enabling dynamic provisioning of Persistent Volumes (PVs). It eliminates the need to manually pre-create PVs and provides flexibility for managing storage across diverse workloads. 

- **Purpose**: Storage Classes define storage backends and their parameters, such as disk types, reclaim policies, and binding modes.  
- **Dynamic Provisioning**: When a Persistent Volume Claim (PVC) is created, Kubernetes uses the referenced Storage Class to automatically provision a corresponding PV.  
- **Flexibility**: Multiple Storage Classes can coexist in a Kubernetes cluster, allowing administrators to tailor storage types for varying application needs (e.g., high-performance SSDs, low-cost storage, etc.).

---

#### **Why Is a Storage Class Required?**

1. Simplifies the storage lifecycle by automating PV creation using dynamic provisioning.  
2. Offers flexibility to define and manage multiple storage tiers.  
3. Optimizes storage resource allocation, especially in environments spanning multiple Availability Zones (AZs).

> StorageClass takes over the role of provisioning PVs dynamically, replacing many of the static configurations you used to define in PVs manually. But not everything from PV moves into the StorageClass—some things like **access modes, size, volumeMode** still come from PVC.

---

### **Example Storage Classes**

Below are two examples of AWS EBS Storage Classes, demonstrating how multiple classes can coexist in the same cluster:

---

```yaml
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: ebs-sc-gp3  # Name of the StorageClass for AWS EBS gp3 volumes.
provisioner: ebs.csi.aws.com  # Specifies the CSI driver for AWS EBS.
parameters:
  type: gp3  # Defines the volume type as gp3 (general purpose SSD with configurable performance).
reclaimPolicy: Delete  # Deletes the provisioned volume when the PVC is deleted.
volumeBindingMode: WaitForFirstConsumer  # Delays volume creation until the Pod is scheduled.
```

---

```yaml
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: ebs-sc-io1  # Name of the StorageClass for AWS EBS io1 volumes.
provisioner: ebs.csi.aws.com  # Specifies the CSI driver for AWS EBS.
parameters:
  type: io1  # Defines the volume type as io1 (high-performance SSD).
reclaimPolicy: Delete  # Deletes the provisioned volume when the PVC is deleted.
volumeBindingMode: WaitForFirstConsumer  # Ensures the volume is created in the same AZ as the Pod.
```

---

#### **Key Points**

1. **Reclaim Policy**:
   - The `Delete` reclaim policy ensures that dynamically provisioned volumes are automatically cleaned up when their corresponding PVCs are deleted.  
   - This prevents orphaned resources and is the most common choice for dynamically provisioned storage.

2. **WaitForFirstConsumer**:

![Alt text](/images/10a.png)
   - In a Kubernetes cluster spanning multiple Availability Zones (AZs), **EBS volumes and EC2 instances are AZ-specific resources**.  
   - If a volume is immediately provisioned in one AZ when a PVC is created, and the Pod using the PVC is scheduled in another AZ, the volume cannot be mounted.  
   - The `WaitForFirstConsumer` mode ensures that the volume is created **only after the Pod is scheduled**, ensuring both the Pod and the volume are in the same AZ.  
   - This prevents inefficiencies and reduces unnecessary costs for resources provisioned in the wrong AZ.

---

## **EKS Storage and Application Deployment using EBS CSI (Collapsed Tier Design)**

Now that we have **EBS CSI drivers installed** and a solid theoretical understanding of StorageClasses, PVCs, and volume binding behavior, let’s move into a practical demonstration.

This module will walk through deploying a **two-tier application** with persistent storage provided by Amazon EBS.

---

### **Architecture Diagram: Collapsed 2-Tier Application on Amazon EKS with EBS-backed MySQL**

![Alt text](/images/10b.png)

This diagram illustrates a collapsed-tier application deployment on an Amazon EKS cluster. The user interacts with the application via a **NodePort service** (`frontend-flask-svc`), which routes external traffic to the `frontend-flask` pod running Flask. This pod serves both the **web interface** and **REST API**.

Internally, the Flask application connects to a MySQL database using the Kubernetes DNS name `mysql-svc`. This service (`ClusterIP`) enables internal-only access to the `mysql` pod, which is backed by an **Amazon EBS volume** (not shown here) for persistent data storage.

**Key Components:**

* **User Access**: Via NodePort on public IP of any EKS worker node
* **frontend-flask Deployment**: Collapsed web + app tier built using Flask (HTML + Python APIs)
* **mysql Deployment**: Stateful tier providing persistent storage with EBS
* **DNS Resolution**: `mysql-svc` resolves internally to the MySQL pod IP
* **Pod-to-Pod Communication**: Achieved through Kubernetes service discovery



---

### **Conceptual Architecture Comparison**

| Layer             | Traditional 3-Tier Architecture      | Current Collapsed Setup (frontend-flask)    |
| ----------------- | ------------------------------------ | ------------------------------------------- |
| **Web Tier**      | React, Angular, Vue (served via CDN) | Flask HTML templates (e.g., `/add` route)   |
| **App Tier**      | Node.js, Django, Java Spring, etc.   | Flask REST APIs with SQLAlchemy ORM         |
| **Database Tier** | Amazon RDS (MySQL/Postgres), Aurora  | MySQL container on EBS volume (`mysql-pvc`) |


---

## **Demo: Deploying a Collapsed 2-Tier Application on Amazon EKS with EBS-Backed Persistent Storage**

> Demonstrating Kubernetes StorageClass, PVC, ConfigMap, and Stateful Deployment Patterns using MySQL and Flask on EKS

### **Step 1: Create StorageClasses**

We will define two EBS-backed StorageClasses: one default `gp3`, and one high-performance `io1`.

```yaml
# Default StorageClass using gp3
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: ebs-sc-gp3
  annotations:
    storageclass.kubernetes.io/is-default-class: "true"
provisioner: ebs.csi.aws.com
parameters:
  type: gp3
volumeBindingMode: WaitForFirstConsumer
reclaimPolicy: Delete
allowVolumeExpansion: true
```

Optional gp3 tuning:

```yaml
parameters:
  type: gp3
  iops: "3000"
  throughput: "125"
```

```yaml
# High-performance storage class using io1
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: ebs-sc-io1
provisioner: ebs.csi.aws.com
parameters:
  type: io1
volumeBindingMode: WaitForFirstConsumer
reclaimPolicy: Delete
allowVolumeExpansion: true
```

**Verify:**

```bash
kubectl get sc
kubectl describe sc ebs-sc-gp3
```

---

### **Step 2: Create PVC for MySQL**

```yaml
# PVC that requests 4Gi of gp3 EBS volume
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: mysql-pvc
spec:
  accessModes:
    - ReadWriteOnce
  storageClassName: ebs-sc-gp3
  resources:
    requests:
      storage: 4Gi
```

> Because we're using `WaitForFirstConsumer`, this PVC will remain in `Pending` until a pod references it.

**Verify:**

```bash
kubectl get pvc
kubectl describe pvc mysql-pvc
```

---


### **Step 3: Create ConfigMap to Initialize MySQL**

```yaml
# ConfigMap used to inject a DB initialization SQL script
apiVersion: v1
kind: ConfigMap
metadata:
  name: mysql-init-cm
data:
  init.sql: |
    CREATE DATABASE IF NOT EXISTS usermgmt;
```

---

#### What are ConfigMaps?

* ConfigMaps allow you to **externalize configuration data** from container images and inject it at runtime.
* This avoids hardcoding environment-specific logic in the image, keeping the image **portable and reusable**.
* ConfigMaps are most commonly consumed in two ways:

  1. **As a mounted volume** — as in this example, where the SQL file is injected into the container’s filesystem.
  2. **As environment variables (EVs)** — for simpler key-value configurations like database credentials, feature toggles, etc.

---

#### **Example: Using ConfigMap as Environment Variables**

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: app-config
data:
  DB_HOST: mysql.default.svc.cluster.local
  DB_NAME: usermgmt
```

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: demo-pod
spec:
  containers:
  - name: demo-container
    image: busybox
    command: ["sh", "-c", "env; sleep 3600"]
    envFrom:
    - configMapRef:
        name: app-config
```

---

#### What This Does:

* The `ConfigMap` defines two environment variables: `DB_HOST` and `DB_NAME`.
* The `demo-pod` loads those variables into the container automatically.
* You can `kubectl exec` into the pod and run `env` to confirm.

You can also write them like this:

```yaml
env:
- name: DB_HOST
  valueFrom:
    configMapKeyRef:
      name: app-config
      key: DB_HOST
- name: DB_NAME
  valueFrom:
    configMapKeyRef:
      name: app-config
      key: DB_NAME
```


---

### **Step 4: Deploy MySQL with EBS Volume**

```yaml
# MySQL deployment that uses the above PVC and ConfigMap
apiVersion: apps/v1
kind: Deployment
metadata:
  name: mysql
spec:
  replicas: 1
  selector:
    matchLabels:
      app: mysql
  strategy:
    type: Recreate
  template:
    metadata:
      labels:
        app: mysql
    spec:
      initContainers:
        - name: init-clean
          image: busybox
          command: ["sh", "-c", "rm -rf /var/lib/mysql/*"]
          volumeMounts:
            - name: mysql-data
              mountPath: /var/lib/mysql
      containers:
        - name: mysql
          image: mysql:8.0
          env:
            - name: MYSQL_ROOT_PASSWORD
              value: mypassword
          ports:
            - containerPort: 3306
          volumeMounts:
            - name: mysql-data
              mountPath: /var/lib/mysql
            - name: mysql-init-script
              mountPath: /docker-entrypoint-initdb.d
      volumes:
        - name: mysql-data
          persistentVolumeClaim:
            claimName: mysql-pvc
        - name: mysql-init-script
          configMap:
            name: mysql-init-cm
```

#### Key Concepts:

* **initContainer** clears old data (important when reusing PVCs during testing).
* `/docker-entrypoint-initdb.d` is a special MySQL mount path for initial SQL scripts.
* Password is supplied via environment variable; this will be moved to AWS Secrets Manager in future lessons.

**Verify:**

```bash
kubectl get deploy mysql
kubectl get pods -l app=mysql
```

---

#### **Why Use `Recreate` Strategy for MySQL?**

Kubernetes Deployments support two rollout strategies:

| Strategy                    | Behavior                                                                      | Suitable For                      |
| --------------------------- | ----------------------------------------------------------------------------- | --------------------------------- |
| **RollingUpdate** (default) | Creates new Pods before terminating the old ones. This ensures zero downtime. | Stateless apps like web frontends |
| **Recreate**                | Terminates all existing Pods before creating new ones.                        | **Stateful apps like databases**  |

---

#### 🔍 Why `Recreate` for Databases?

* **`ReadWriteOnce` (RWO)** – allows **one node** to mount the volume **at a time** in **read-write mode**.

  * **Multiple Pods on the same node** **can share** the volume (because it’s mounted once at the node level).
  * However, this is risky for databases as concurrent Pod restarts or upgrades could cause:

    * Unintentional volume sharing
    * File corruption or lock conflicts
* With `RollingUpdate`, Kubernetes may try to bring up a new Pod while the old one is still running — leading to **volume mount conflicts**.
* `Recreate` ensures the **old Pod is terminated before the new Pod is scheduled**, avoiding any volume contention.

💡 **Important Note on Databases**:
In most production setups, **only the primary (master)** database instance should have **write access** to the storage volume.
Additional **read replicas** (or mirrors) are typically configured to **only read** data and **do not mount the same volume**. If the master fails, **failover mechanisms** promote a replica to become the new primary — at which point it would need its own clean, exclusive volume or remounting logic.


---

So, in our MySQL deployment:

```yaml
strategy:
  type: Recreate
```

…ensures smooth rollout **without competing over the EBS volume** and is the correct strategy for **stateful, single-writer workloads**.

---

### **Step 5: Expose MySQL via ClusterIP Service**

```yaml
# Internal-only MySQL service
apiVersion: v1
kind: Service
metadata:
  name: mysql-svc
spec:
  selector:
    app: mysql
  ports:
    - port: 3306
```

* This creates an internal DNS entry `mysql-svc.default.svc.cluster.local`
* Will be used by the `frontend-flask` application to connect to the DB

**Verify:**

```bash
kubectl get svc mysql-svc
```

---

### **Step 6: Verify Database Creation**

```bash
kubectl run -it --rm --image=mysql:8.0 --restart=Never mysql-client \
  -- mysql -h mysql-svc -uroot -pmypassword
```

Within the MySQL shell:

```sql
SHOW DATABASES;
USE usermgmt;
SHOW TABLES;
```

You should see the `usermgmt` database created by the `init.sql` file injected via the ConfigMap.

---

### **Step 7: Deploy the frontend-flask Container**

```yaml
# Collapsed web + app tier written in Flask
apiVersion: apps/v1
kind: Deployment
metadata:
  name: frontend-flask
spec:
  replicas: 1
  selector:
    matchLabels:
      app: frontend-flask
  template:
    metadata:
      labels:
        app: frontend-flask
    spec:
      containers:
        - name: frontend-flask
          image: varunjoshi0404/flask-usermgmt-api:1.0
          imagePullPolicy: Always
          ports:
            - containerPort: 8080
          env:
            - name: DB_HOST
              value: mysql-svc
            - name: DB_PORT
              value: "3306"
            - name: DB_NAME
              value: usermgmt
            - name: DB_USER
              value: root
            - name: DB_PASSWORD
              value: mypassword
```

#### Note on Collapsed Tier Design:

This `frontend-flask` deployment serves:

* HTML pages (browser-based form for user entry)
* REST APIs (for automation and testing)

This simplifies our architecture for demonstration purposes but is modular enough to split in later lessons.

**Verify:**

```bash
kubectl get deploy frontend-flask
kubectl get pods -l app=frontend-flask
```

---

### **Step 8: Expose frontend-flask via NodePort**

```yaml
# NodePort service for temporary external access
apiVersion: v1
kind: Service
metadata:
  name: frontend-flask-svc
spec:
  selector:
    app: frontend-flask
  type: NodePort
  ports:
    - port: 8080
      targetPort: 8080
      nodePort: 31000  # Chosen for predictability
```

* This allows us to access the Flask app from the browser during the demo.
* Later, we will replace this with an Ingress Controller + AWS ALB for managed load balancing.

---

### **Step 9: Access and Test the Application**

#### **Access via Browser or API**

First, retrieve the public IP of any EC2 node in your EKS cluster:

```bash
kubectl get nodes -o wide
```

Once you have the `<NodeIP>`, you can test the application using the following URLs:

| URL                              | Description                    |
| -------------------------------- | ------------------------------ |
| `http://<NodeIP>:31000/health`   | Basic application health check |
| `http://<NodeIP>:31000/db_check` | Database readiness check       |
| `http://<NodeIP>:31000/add`      | HTML form to add a new user    |
| `http://<NodeIP>:31000/users`    | Returns all users in JSON      |

> **Note**: Ensure port `31000` is open in the security group associated with your worker nodes.

---

#### **Access MySQL Directly from a Pod**

You can also verify the backend directly by connecting to the MySQL container using a client pod:

```bash
kubectl run -it --rm --image=mysql:8.0 --restart=Never mysql-client \
  -- mysql -h mysql-svc -uroot -pmypassword
```

Inside the MySQL shell, run:

```sql
USE usermgmt;
SELECT * FROM user;
```

This will return all user records from the `user` table in the `usermgmt` database.


---

### **What Needs Improvement?**

Although we’ve successfully deployed a collapsed 2-tier application on Kubernetes—and you may still find real-world applications following this design—it’s important to recognize and address its current limitations. These gaps could cause instability or inefficiencies, especially in production environments.

Here are a few key areas we will improve:

* **Startup Dependency Issue**:
  The application pod sometimes restarts (2–4 times) because it tries to connect to the MySQL database **before it’s fully ready**. This can be avoided by introducing an **`initContainer`** that waits for the database to become available before starting the main app container.

* **Missing Health Checks**:
  Currently, we haven’t defined **readiness or liveness probes**. Without these, Kubernetes has no way to detect whether the app is healthy or ready to serve traffic, which can result in failed requests or downtime.

* **Default Namespace Deployment**:
  We deployed both the frontend and database in the **`default` namespace**, which is discouraged for production-grade applications. Organizing workloads into **logical namespaces** improves security, isolation, and resource management.

* **No Resource Requests or Limits**:
  The pods have **no CPU or memory boundaries** set. This makes them vulnerable to the **"noisy neighbor"** problem—where one pod consumes excessive resources, starving others on the same node.

---

### **What’s Coming Next**

In the next 2–3 sessions, we’ll address each of these issues systematically:

* Add `initContainers` for dependency checks
* Define liveness and readiness probes
* Move workloads into a dedicated namespace
* Apply resource requests and limits

Later in the course, we’ll evolve this app further using:

* **Amazon RDS** for a managed MySQL backend
* **AWS ALB Ingress Controller** for scalable external access
* **Horizontal & Vertical Pod Autoscalers** for dynamic scaling
* **Cluster Autoscaler** for optimizing infrastructure cost and efficiency

Stay tuned—this journey from basic to production-ready Kubernetes is just getting started.

---


