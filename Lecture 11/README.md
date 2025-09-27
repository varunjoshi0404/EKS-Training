# Lecture 11: Kubernetes Secrets, Multi-Container Pods, Probing & Namespaces with Amazon EKS

---

### **What is a Kubernetes Secret?**

A **Secret** is a Kubernetes object used to store and manage sensitive information. Secrets are base64-encoded and can be made more secure by:

- Enabling encryption at rest
- Limiting RBAC access to Secrets
- Using external secret managers like HashiCorp Vault, AWS Secrets Manager, or Sealed Secrets

Accessible to Pods via:
  1. **Environment variables**
  2. **Mounted volumes (as files)**
  3. **Command-line arguments** (less common)

> Note: By default, Kubernetes stores secrets unencrypted in `etcd`. It is recommended to enable encryption at rest for better security.

---

### **Important Distinction: Encoding vs. Encryption**

It's crucial to understand that **Kubernetes Secrets use base64 *encoding*, not encryption**.  
This means the data is **obfuscated but not secured**. Anyone who gains access to the Secret object can **easily decode** it.

**Why Use Encoding (e.g., base64)?**

Encoding is useful when you want to **hide the data from casual observation**, such as:

- Preventing someone looking over your shoulder from instantly seeing a password.
- Making binary data safe to transmit in systems that expect text.

However, **encoding is not encryption**. It's **not secure** by itself.  
> Anyone who has access to your encoded data can easily decode it.

For example, base64 is **reversible** using a simple decoding command.  
If you need to **protect sensitive data**, you should use **encryption** or a Kubernetes **Secret**, which at least provides better handling and access controls.

We'll see how to **encode** and **decode** in the demo section.

---

### **Encoding vs. Encryption**

| Feature         | Encoding                        | Encryption                           |
|----------------|----------------------------------|--------------------------------------|
| **Purpose**     | Data formatting for safe transport | Data protection and confidentiality |
| **Reversible**  | Yes (easily reversible)          | Yes (only with the correct key)      |
| **Security**    | Not secure                       | Secure                                |
| **Use Case**    | Data transmission/storage compatibility | Protect sensitive data (passwords, tokens) |
| **Example**     | Base64, URL encoding             | AES, RSA, TLS                        |
| **Tool Needed to Decode** | None (any base64 tool)         | Requires decryption key              |

---

> **Note:** If you need to store sensitive data securely, consider enabling **encryption at rest** for Secrets in Kubernetes and restrict access using RBAC.

---


## **Demo: Securing Database Credentials Using Kubernetes Secrets**

In our earlier implementation, we hardcoded the database password directly in the `frontend-flask` and `mysql` deployment manifests using plain text:

`mysql` deployment
```yaml
- name: MYSQL_ROOT_PASSWORD
  value: mypassword
```

`frontend-flask` deployment
```yaml
- name: DB_PASSWORD
  value: mypassword
```

This is **not a secure practice**, especially in production environments or when storing YAML manifests in version control.



> Note: For even stronger protection, Secrets be integrated with **AWS Secrets Manager** using **IRSA** (IAM Roles for Service Accounts).

---

### **Step 1: Create the Secret**

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: db-secret
type: Opaque
data:
  DB_PASSWORD: bXlwYXNzd29yZA==  # base64 for "mypassword"
  DB_ROOT_PASSWORD: bXlwYXNzd29yZA== # base64 for "mypassword"
```

---

### **How to Encode and Decode Base64 Values**

Base64 is often used in Kubernetes manifests (e.g., for Secrets). Below are ways to **generate** and **decode** base64 values.

---

#### **Encode a Value (e.g., password)**

Use any of the following:

* **macOS / Linux Terminal:**

  ```bash
  echo -n "mypassword" | base64
  ```

* **Git Bash on Windows (should work):**

  ```bash
  echo -n "mypassword" | base64
  ```

* **Online Tool:**

  [https://www.base64encode.org/](https://www.base64encode.org/)

---

#### **Decode a Base64 Value**

To get the original plain text from a base64-encoded string:

* **macOS / Linux Terminal:**

  ```bash
  echo 'bXlwYXNzd29yZA==' | base64 --decode
  ```

* **Git Bash on Windows:**

  ```bash
  echo 'bXlwYXNzd29yZA==' | base64 --decode
  ```

* **Online Tool:**

  [https://www.base64decode.org/](https://www.base64decode.org/)

> **Tip**: Always use `-n` with `echo` during encoding to avoid newline characters sneaking into your encoded output.


---

### **Step 2: Update Deployments to Use the Secret**

We'll now update both the `mysql` and `frontend-flask` deployments to **reference the password from the secret**.

---

### **MySQL Deployment (Updated)**

```yaml
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
              valueFrom:
                secretKeyRef:
                  name: db-secret
                  key: DB_PASSWORD
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

---

### **frontend-flask Deployment (Updated)**

```yaml
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
              valueFrom:
                secretKeyRef:
                  name: db-secret
                  key: DB_PASSWORD
```

---

### **Why Multi-Container Pods?**
![Alt text](/images/12a.png)

**Why not just use separate pods?**  
In Kubernetes, pods provide a **shared execution environment**, making them ideal for situations where containers need to work **tightly together**. For instance:
1. Containers within a pod can **share network and storage resources**, enabling close communication.
2. They can coordinate **startup and shutdown processes** effectively.
3. Multi-container pods reduce **operational complexity** by grouping functionality into one entity (instead of scattered pods).

---

### **What Are Multi-Container Pods?**
A **multi-container pod** is simply a pod containing **more than one container**. These containers:
- Share **network namespaces** (e.g., communicate via `localhost`).
- Can access **shared storage volumes** (if defined in the pod spec).
- Work together to fulfill a specific purpose.

Typically, a **multi-container pod** includes **one primary container** (the main application) and one or more **helper containers** (such as sidecars, ambassadors, or adapters).

---

### **Shared Resources in Multi-Container Pods**

| **Resource**             | **Shared in Pod?**    | **Explanation**                                                                                                                      |
|-------------------------|----------------------|---------------------------------------------------------------------------------------------------------------------------------------|
| **Network Namespace**    | ✅ **Yes**            | - All containers share the **same network namespace**.<br>- Communicate over **localhost** or the pod's IP.<br>- Example: Helper container accesses main container on `localhost:<port>`. |
| **Volumes/Storage**      | ✅ **Yes**            | - Volumes are defined at the **pod level**.<br>- Any container mounting the volume can access the data.<br>- Example: Sidecar reads logs written by main container. |
| **PID Namespace**        | ❌ **No**             | - Each container has its **own process namespace**.<br>- Processes in one container are **isolated** from others unless configured otherwise (e.g., `hostPID`). |
| **Filesystem (Root FS)** | ❌ **No**             | - Every container has its **own root filesystem**.<br>- Shared access only possible via **explicitly mounted volumes**. |
| **Environment Variables**| ❌ **No**             | - Environment variables are scoped to each container.<br>- Can be shared across containers using **ConfigMaps** or **Secrets** if needed. |                         |

---

### **Multi-Container Pod Patterns**

![Alt text](/images/12a.png)
![Alt text](/images/12b.png)

Multi-container pods generally follow four key patterns:

#### **1. Init Containers**

Init containers are **startup containers** designed to run before the main application container. They perform initialization tasks like:
- **Preparing configurations** or environments.
- **Waiting for dependencies** like APIs or databases to be ready.
- **Performing pre-checks** to ensure proper startup conditions.

#### **How Init Containers Work**:
- They always **run to completion** (success or failure).
- Run **sequentially**, one after the other.
- If any init container fails, the main container **never starts**.

#### **Use Cases:**
Common preconditions include:
1. **Database readiness**: Verify connection or schema migration before app startup.
2. **External API health checks**: Ensure critical APIs are reachable.
3. **File or directory initialization**: Create required directories or files for the app.
4. **Fetching secrets/configurations**: Download secrets from external systems.
5. **Cleaning up temporary files**: Ensure temporary files from previous runs are removed.

---

#### **2. Sidecar Pattern**

The **Sidecar Pattern** involves containers that **extend or complement the main container's functionality**. Sidecars run alongside the primary container and operate independently.

#### **Use Cases**:
1. **Logging**: Collect logs and send them to central systems (e.g., Fluentd, Fluent Bit).
2. **Monitoring**: Export metrics for tools like Prometheus.
3. **Proxying**: Handle incoming traffic (e.g., Envoy, Istio, AWS App Mesh).
4. **Data synchronization**: Sync files or configurations to external locations.

#### **Example:**
A sidecar proxy can intercept network traffic flowing into the pod, provide telemetry data, or encrypt the communication.

---

#### **3. Ambassador Pattern**

The **Ambassador Pattern** involves containers that act as **proxies between the pod and external systems**. Unlike the sidecar pattern, the ambassador is focused on handling **external communication**.

#### **Use Cases**:

1. **API Gateways**: Proxy external client requests to internal services, routing traffic based on paths or headers (e.g., `/api/orders` to Order Service).  
2. **Connection Management**: Optimize and pool connections to external resources like databases or APIs, ensuring efficient usage (e.g., managing PostgreSQL connections).  
3. **Security**: Terminate TLS or add authentication layers (e.g., handling OAuth token validation before forwarding requests).  

#### **Examples**:
- An **ambassador container** can proxy requests to databases (e.g., Amazon RDS), external queues (e.g., Amazon SQS), or cloud services like Azure API Gateway.

---

#### **Sidecar vs. Ambassador Proxying**
| **Aspect**         | **Sidecar Pattern**                              | **Ambassador Pattern**                           |
|---------------------|-------------------------------------------------|-------------------------------------------------|
| **Scope**          | Internal cluster communication                  | External system communication                   |
| **Primary Use Case**| Enhance the functionality of the main container | Mediate communication between pod and external systems |
| **Example**         | Envoy managing traffic between microservices    | Ambassador proxying requests to external APIs   |

---

#### **4. Adapter Pattern**

The **Adapter Pattern** involves containers that **transform or normalize data** between the main container and an external system. These are ideal for applications requiring data compatibility adjustments.

#### **Use Cases**:
1. **Metric transformation**: Convert custom application metrics into standard formats like Prometheus.
2. **Log normalization**: Process and format logs for external systems.

#### **Example:**
An adapter container collects JSON-based metrics from the app, converts them to Prometheus format, and makes them available for scraping.

---

## **Differences: Init Containers vs Sidecar, Ambassador, Adapter Containers**

| **Aspect**                     | **Init Containers**                                                                                      | **Sidecar / Ambassador / Adapter Containers**                                                                   |
|--------------------------------|---------------------------------------------------------------------------------------------------------|---------------------------------------------------------------------------------------------------------------|
| **Lifecycle**                  | **Run to completion before main container starts**                                                       | **Run alongside main container**, continue as long as the pod runs                                             |
| **Order of Execution**         | Always run **before** the main container, in sequence if multiple                                         | Start **in parallel** with the main container                                                                  |
| **Dependency on Success**      | **Main container won’t start unless all init containers complete successfully**                           | Main container can run **independently of helper containers (but may rely on their functionality)**            |
| **Restart Behavior**           | **Re-run only if they fail before completion**                                                            | Restart policies apply same as main container (`Always`, `OnFailure`, etc.)                                    |
| **Purpose**                    | **Setup, preparation, environment bootstrapping, preconditions check**                                    | Enhance, complement, or adapt runtime behavior of the main container                                           |
| **Resource Consumption**       | Consume resources **temporarily**, freed once completed                                                   | Consume resources **throughout the pod’s lifetime**                                                            |
| **Common Use-Cases**           | - Database migrations<br>- Configuration fetch<br>- Waiting for dependencies<br>- Permission setup        | - Log collection<br>- Proxying (Service Mesh)<br>- External communication handling (Ambassador)<br>- Metrics/log format adaptation |
| **Visibility to Main Container**| Prepare **shared volumes or environment**, not visible as active containers                              | Main container and helpers can interact **live** via shared network & volumes                                  |
| **Network Behavior**           | Share network namespace, but only active until completion                                                 | Share network namespace, **actively communicate during pod lifetime**                                         |
| **Fail Impact**                | **Pod won’t proceed if init fails**                                                                      | If they fail, **pod continues**, but functionality (e.g., logging, proxying) may degrade                        |

---


## What are Health Probes?

![Alt text](/images/12c.png)

In Kubernetes, health probes are used to check the status of applications running inside pods. These probes help Kubernetes ensure that only healthy pods are receiving traffic, and unhealthy pods are either given time to recover or restarted as necessary. The **kubelet** is responsible for performing these probes.

### **Types of Health Probes**

![Alt text](/images/12d.png)

1. **Readiness Probes (RP)**
Determines if the application is **ready** to handle traffic. If this probe fails, the Pod is marked as **"Not Ready"** and is removed from Service endpoints, but the container itself is not restarted.
   - **Purpose**: Checks if a container is **ready to start accepting traffic**.
   - **Behavior**:
     - When the readiness probe fails, the pod is removed from the service's load balancer, but **the container is not restarted**.
   - **Key Advantage**: Prevents routing traffic to containers that are temporarily unable to serve requests due to initialization delays or resource constraints.
   - **Example**:
     ```yaml
      readinessProbe:
        httpGet:
          path: /readyz
          port: 8080
        initialDelaySeconds: 5  # Wait 5 seconds after container starts before probing
        periodSeconds: 10       # Probe every 10 seconds
     ```

      - **Explanation:**
        - Checks if the application is ready to serve traffic.
        - HTTP GET request is sent to /readyz on port 8080.
        - Starts after an initial delay of 5 seconds.
        - If probe fails, the pod is temporarily removed from Service endpoints (no restart).
        - Once probe passes, pod starts receiving traffic.
    - **Use Case**:
      - A database connection might temporarily fail. During this time, the readiness probe ensures that traffic is not sent to the affected pod.

---

2. **Liveness Probes (LP)**
The **kubelet** uses liveness probes to know when to restart a container. For example, liveness probes could catch a deadlock, where an application is running, but unable to make progress. Restarting a container in such a state can help to make the application more available despite bugs.

   - **Purpose**: Checks if a container is **alive and functioning correctly**.
   - **Behavior**:
     - When the liveness probe fails, **the pod is restarted**.
   - **Key Advantage**: Helps recover from **irrecoverable failures**, such as deadlocks or unresponsive applications.
   - **Example**:
     ```yaml
      livenessProbe:
        exec:
          command:
          - cat
          - /tmp/healthy
        initialDelaySeconds: 3  # Start checking 3 seconds after the container starts
        periodSeconds: 5        # Check every 5 seconds
     ```

     - **Explanation:**
        - Verifies if the application is still alive.
        - Executes `cat /tmp/healthy` inside the container.
        - If this command fails (e.g., file missing), the liveness probe fails.
        - **Kubelet will restart the container automatically** to recover from the failure.
   - **Use Case**:
     - Detects and restarts applications stuck in an unrecoverable state (e.g., infinite loop or deadlock).
---
3. **Startup Probes**
Ensures that the container has enough time to initialize the application. Until this probe succeeds, **liveness and readiness probes** are not triggered.

   - **Purpose**: Used for **legacy or slow-starting applications** that take variable amounts of time to initialize.
   - **Problem Solved**: The `initialDelaySeconds` parameter cannot always capture the correct startup time for such applications. Setting it too high causes unnecessary delays, and too low leads to premature restarts.
   - **Behavior**:
     - When a startup probe is defined, **liveness and readiness probes do not start** until the startup probe succeeds.
   - **Example**:
     ```yaml
     startupProbe:
      httpGet:
        path: /healthz
        port: 8080
      failureThreshold: 30  # Kubernetes (via Kubelet) will attempt the probe up to 30 times before failing
      periodSeconds: 10     # Probe runs every 10 seconds
     ```
      - **Explanation:**
        - This probe is responsible for determining when the application has successfully started.
        - It sends an HTTP GET request to /healthz on port 8080.
        - It will try every 10 seconds, up to 30 times (total grace period = 300 seconds).
        - If all 30 attempts fail, Kubernetes will mark the pod as failed and stop trying.
      - No restart happens because the app never started properly.
     This configuration ensures the app has **up to 5 minutes** (30 * 10 = 300 seconds) to initialize.

---

### **Why Configure Both Readiness and Liveness Probes?**

While it may seem that configuring only liveness probes is enough, **best practice dictates using both** for the following reasons:
- **Readiness Probes (RP)**:
  - Do not restart a failing pod; they just stop sending traffic to it.
  - This ensures that **transient issues** (e.g., high load or temporary database unavailability) do not unnecessarily trigger a restart.
  - Pods can continue running and recover without interruption.
- **Liveness Probes (LP)**:
  - Designed for **critical, irrecoverable issues** where a restart is the only solution.
  - Ensures that **dead or hung pods are recreated**, preserving application availability.

**Key Insight**:
- Without RP: Traffic may still be sent to pods experiencing temporary failures, degrading user experience.
- Without LP: Pods stuck in fatal states will remain idle and waste resources.

---

### Probe Timer Configuration Parameters

| **Property**          | **Meaning**                                                    | **Default Value** | **Example**                              |
|----------------------|----------------------------------------------------------------|-------------------|------------------------------------------|
| `initialDelaySeconds` | Wait time before first probe starts after container starts     | `0` seconds       | `initialDelaySeconds: 5` → starts after 5 sec |
| `periodSeconds`       | Time interval between probe attempts                           | `10` seconds      | `periodSeconds: 10` → probes every 10 sec   |
| `timeoutSeconds`      | Max wait time for probe response                               | `1` second        | `timeoutSeconds: 2` → fail if no reply in 2 sec |
| `successThreshold`    | No. of consecutive successes needed to mark successful         | `1`               | `successThreshold: 3` → pass after 3 successes |
| `failureThreshold`    | No. of consecutive failures before marking probe as failed     | `3`               | `failureThreshold: 5` → fail after 5 failures  |

---

### **Behavior of RP, LP, and Startup Probes with Multi-Container Pods**

1. **Pod and Container Relationship**:
   - A pod in Kubernetes can host multiple containers.
   - The **pod's status reflects the worst state of any container** within it:
     - Common errors include:
       - **`Error`**: Indicates a general runtime issue (e.g., application crash or misconfiguration).
       - **`ImagePullBackOff`**: Happens when Kubernetes cannot pull the specified container image (e.g., due to incorrect image name or registry authentication issues).
       - **`CrashLoopBackOff`**: Occurs when a container starts, crashes, and continuously restarts in a loop.
       - **`RunContainerError`**: A catch-all for runtime errors (e.g., failure to execute the container command).
     - A pod is marked **"Running"** only when all containers within it are successfully running.

2. **Startup Probe**:
   - Each container's startup probe runs independently.
   - If the startup probe for one container fails, **only that container is affected**, and liveness/readiness probes are not triggered for it. Other containers proceed unaffected.

3. **Readiness Probe**:
   - Readiness probes determine whether the pod is ready to serve traffic.
   - If the readiness probe fails for **one container**, the **entire pod** is marked **"Not Ready"** to ensure no partial or unreliable service is provided.
   - Failed readiness probes only affect traffic routing and do not restart the container.

4. **Liveness Probe**:
   - Liveness probes are container-specific.
   - If the liveness probe fails for one container, **only that container is restarted** by the **Kubelet**, while other containers remain unaffected.

5. **Pod Status Summary**:
   - The **pod's status reflects the most severe state** of any container:
     - **Running**: All containers are running properly.
     - **Error**: At least one container experienced a runtime failure (e.g., application crash).
     - **ImagePullBackOff**: Kubernetes is unable to pull the image for at least one container.
     - **CrashLoopBackOff**: A container repeatedly crashes and restarts.
     - **RunContainerError**: General runtime error for one or more containers.
   - If a **readiness probe fails** for even one container, the pod is marked **"Not Ready"**.

---

### **Kubernetes Health Probes: Comprehensive Comparison**

Here is the revised table with the important words and concepts **bolded** to highlight key details:

| **Aspect**                     | **Startup Probe**                                                                | **Readiness Probe**                                                               | **Liveness Probe**                                                                |
|--------------------------------|----------------------------------------------------------------------------------|----------------------------------------------------------------------------------|----------------------------------------------------------------------------------|
| **Purpose**                    | Ensure **slow-starting apps** are given enough time to start                     | Check if the pod is **ready to receive traffic**                                 | Check if the pod is **alive and functioning properly**                           |
| **When Does It Start?**        | **Immediately** after container starts                                           | Starts **when the pod enters the "Running" state** and **after Startup Probe succeeds (if configured)** | Starts **when the pod enters the "Running" state** and **after Startup Probe succeeds (if configured)** |
| **Failure Behavior**           | Pod is **killed & restarted** after failure threshold is exceeded during startup | Pod is **marked unready** and removed from **Service load balancers**; not restarted | Pod is **killed & restarted** after failure threshold exceeded                   |
| **Effect on Pod Traffic**      | **No direct effect**                                                             | **Stops sending traffic** to the pod                                             | **No direct effect** on traffic                                                  |
| **Common Use Case**            | **Legacy apps**, slow-booting apps with unpredictable startup times              | Apps needing time to **initialize external dependencies or configurations**       | Recover from **stuck apps**, **deadlocks**, or **memory leaks**                  |
| **Recovery Mechanism**         | Pod is **restarted** during initialization                                       | **No restart**; waits for probe to pass                                          | Pod is **restarted**                                                             |
| **Runs Until**                 | Probe **succeeds** → switches control to **RP & LP**                             | Runs **continuously** throughout the pod's lifecycle                             | Runs **continuously** throughout the pod's lifecycle                             |
| **Starts Again After Restart?**| **Yes**                                                                          | **Yes**                                                                          | **Yes**                                                                          |
| **Relation to Service Traffic**| **None**                                                                         | Directly **influences Service endpoints**                                        | **None**                                                                         |
| **Frequency (Default)**        | Configurable (e.g., `periodSeconds`, `failureThreshold`)                          | Configurable (e.g., `initialDelaySeconds`, `periodSeconds`)                      | Configurable (e.g., `initialDelaySeconds`, `periodSeconds`)                      |
| **Mechanisms Supported**       | **HTTP GET**, **TCP Socket**, **Exec Command**                                   | **HTTP GET**, **TCP Socket**, **Exec Command**                                   | **HTTP GET**, **TCP Socket**, **Exec Command**                                   |
| **Best Practices**             | Use for **apps with unpredictable boot times**                                   | **Always** use in production to avoid sending traffic to **unready pods**        | **Always** use to automatically recover from **unrecoverable failures**          |
| **Administrative Benefit**     | Avoid unnecessary **premature restarts** for **slow-start apps**                 | Prevent unnecessary **load and requests** hitting pods that **aren't ready**     | Ensures **automatic recovery** from **failures**                                 |
| **Impact on Resources**        | Uses **CPU/memory** during startup period                                        | Pod consumes resources but doesn't receive traffic if **unready**                | Pod consumes resources until **restarted**                                       |
| **Pod State While Failing**    | Pod **restarts** after failure                                                   | Pod **stays running** but removed from **Service traffic**                       | Pod **restarts** after failure                                                   |
| **Typical Example**            | **Java apps** taking >60s to start, **legacy monoliths**                         | App needs **DB connection** or **configuration loaded** before accepting requests | **Deadlock**, app frozen, **memory leak**, or stuck threads                      |

---

### **Probe Mechanisms**

![Alt text](/images/12f.png)

Kubernetes provides **three mechanisms** for performing health probes:

1. **HTTP GET Requests**:
   - The kubelet sends an HTTP GET request to a specified endpoint.
   - **Success**: Status codes 200–399.
   - **Failure**: Any other status code.
   - **Example**:
     ```yaml
     livenessProbe:
       httpGet:
         path: /healthz
         port: 8080
       initialDelaySeconds: 3
       periodSeconds: 5
     ```
     In this case, the app responds with HTTP `200` to indicate health.

2. **TCP Socket**:
   - The kubelet checks if a TCP connection can be established to a specified port.
   - **Success**: Connection is successful.
   - **Failure**: Connection cannot be established.
   - **Example**:
     ```yaml
     readinessProbe:
       tcpSocket:
         port: 3306
       initialDelaySeconds: 10
       periodSeconds: 5
     ```
     This is useful for services like databases that listen on specific ports.

3. **Command Execution**:
   - The kubelet runs a specified command inside the container.
   - **Success**: Command exits with code `0`.
   - **Failure**: Command exits with a non-zero code.
   - **Example**:
     ```yaml
     livenessProbe:
       exec:
         command:
         - cat
         - /tmp/healthy
       initialDelaySeconds: 5
       periodSeconds: 10
     ```
     In this example, the app creates a `/tmp/healthy` file when healthy. If the file is missing, the probe fails.

---

## Demo: Using Init Containers, Readiness & Liveness Probes in Application Workloads

### **Objective**

In this section, we'll enhance our `frontend-flask` deployment to be more **robust and production-ready** by introducing:

* An **Init Container** that ensures the database is reachable before the app starts
* A **Readiness Probe** to ensure the app receives traffic only when it's fully ready
* A **Liveness Probe** to detect and recover from unresponsive or unhealthy app states

These patterns are industry-standard and critical for building resilient, observable applications on Kubernetes.

---

## Step 1: Enhanced Deployment Manifest

```yaml
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
      initContainers:
        - name: wait-for-mysql
          image: busybox:1.35
          command:
            - sh
            - -c
            - |
              echo "[INFO] Waiting for MySQL to become available at mysql-svc:3306..."
              until nc -z -v -w30 mysql-svc 3306; do
                echo "[WAITING] Still waiting for DB... retrying in 5s"
                sleep 5
              done
              echo "[SUCCESS] DB is now reachable. Proceeding with app startup."
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
              valueFrom:
                secretKeyRef:
                  name: db-secret
                  key: DB_PASSWORD
          readinessProbe:
            httpGet:
              path: /health
              port: 8080
            initialDelaySeconds: 5
            periodSeconds: 10
            timeoutSeconds: 2
            failureThreshold: 3
          livenessProbe:
            httpGet:
              path: /health
              port: 8080
            initialDelaySeconds: 10
            periodSeconds: 20
            timeoutSeconds: 2
            failureThreshold: 5
```

---

## Explanation

### **1. Init Container: `wait-for-mysql`**

**Purpose:**
Prevents the main application container from starting until the MySQL database is confirmed to be reachable.

**How it works:**
Uses a lightweight `busybox` image to run a loop that checks if the MySQL service (`mysql-svc:3306`) is accessible using `nc` (netcat). If the database isn’t ready, it waits and retries every 5 seconds until success.

**Command Breakdown:**

```bash
echo "[INFO] Waiting for MySQL to become available at mysql-svc:3306..."
until nc -z -v -w30 mysql-svc 3306; do
  echo "[WAITING] Still waiting for DB... retrying in 5s"
  sleep 5
done
echo "[SUCCESS] ✅ DB is now reachable. Proceeding with app startup."
```

| Line                   | Meaning                                                                                  |
| ---------------------- | ---------------------------------------------------------------------------------------- |
| `echo ...`             | Prints a log message to indicate the DB wait has started.                                |
| `until nc ...`         | Tries to open a TCP connection to MySQL (`mysql-svc:3306`). If it fails, loop continues. |
| `echo "[WAITING] ..."` | Logs a retry message if DB isn’t up yet.                                                 |
| `sleep 5`              | Waits 5 seconds before retrying.                                                         |
| `done`                 | Ends the loop when the DB becomes reachable.                                             |
| `echo "[SUCCESS] ..."` | Confirms success and allows the app to start.                                            |

**Logs:**

```
[INFO] Waiting for MySQL to become available at mysql-svc:3306...
[WAITING] Still waiting for DB... retrying in 5s
[WAITING] Still waiting for DB... retrying in 5s
[SUCCESS] ✅ DB is now reachable. Proceeding with app startup.
```

---

### **2. Readiness Probe**

**Purpose:**
Tells Kubernetes **when the application is ready** to receive traffic.

**How it works:**
Periodically sends an HTTP GET request to the `/health` endpoint on port `8080`. The pod is considered "ready" only if it returns a `200 OK` response.

**Effect:**
Until this probe passes, Kubernetes **does not send any traffic** to the pod via the service — ensuring users only reach a working instance.

---

### **3. Liveness Probe**

**Purpose:**
Detects if the application becomes **unresponsive or locked up** after it has started.

**How it works:**
Kubernetes continuously probes `/health` on port `8080`. If the endpoint repeatedly fails or times out, Kubernetes assumes the app is unhealthy.

**Effect:**
Triggers an **automatic container restart** if the probe fails the configured number of times — helping recover from stuck states or deadlocks.

---

### **Best Practice (for Web/API Containers)**

> Use `httpGet` probes for readiness and liveness in web and API-based applications.
> This ensures you're not just checking if the port is open — you're verifying that the **real application logic is functioning correctly**.

---

## **What Are Namespaces in Kubernetes?**
A **namespace** in Kubernetes is a **logical partition** within a cluster that helps organize and isolate **resources**. Namespaces enable:  

- **Isolation & Security:** Separate workloads to prevent unwanted interactions.  
- **Avoiding Naming Conflicts:** Resources with the **same name** can exist in **different namespaces**.  
- **Resource Management:** Apply **resource quotas** and **limits** at the namespace level.  
- **Application Segregation:** Separate **environments** (e.g., **dev**, **test**, **prod**) or **projects**.  
- **Organizational Clarity:** Manage resources by **teams**, **departments**, or **projects**.  

---

## **Analogy to Understand Namespaces**  

![Alt text](/images/11a.png)

Imagine a **large house** where **four families** live together:  

- Without namespaces, all families share **common spaces**, leading to **no privacy, security, or organization**.  
- When you **create rooms** for each family, each family has its **own space**, improving **isolation, security, and organization**.  

### **Relating to Kubernetes:**  
- The **large house** is the **Kubernetes cluster**.  
- The **families** are **applications** or **workloads**.  
- **Rooms** are **namespaces**, providing **segregation and control** over resources.  

---

## **Why Use Namespaces?**
- 🛡️ **Security:** Limit access and apply **network policies**.  
- 🚦 **Resource Management:** Define **quotas** and **limits** for CPU and memory.  
- 🎯 **Environment Management:** Isolate **development**, **testing**, and **production** environments.  
- 📦 **Multi-Tenancy:** Host **multiple applications** in the **same cluster** without conflicts.  
- 🧹 **Simplification:** Manage **related resources together**.  

---

## **Default Namespaces in Kubernetes**  
When you run `kubectl get namespaces`, you’ll see these **default namespaces**:  

| **Namespace** | **Purpose** |
|---------------|--------------|
| `default`    | Kubernetes includes this namespace so that you can start using your new cluster without first creating a namespace. |
| `kube-system` | The namespace for objects created by the Kubernetes system. Holds **Kubernetes control plane components** (e.g., **kube-dns**, **kube-proxy**). |
| `kube-public` | This namespace is readable by all clients (including those not authenticated). **Publicly accessible data**, primarily used for **cluster information**. |
| `kube-node-lease` | **Heartbeats of nodes** in the cluster, used by the **control plane** for **node health**. |

**Note:** In **KIND** (**K**ubernetes **IN** **D**ocker) clusters, the local-path-storage namespace is created by default to support persistent storage using the Local Path Provisioner.

---

## **Working with Namespaces**

### **Creating Namespaces**

#### **1. Imperative Way:**
```sh
kubectl create namespace app1-ns
```

#### **2. Declarative Way:**
```yaml
# app1-ns.yaml
apiVersion: v1
kind: Namespace
metadata:
  name: app1-ns
```

```sh
kubectl apply -f app1-ns.yaml
```

---

### **Viewing and Deleting Namespaces**

#### **View All Namespaces:**
```sh
kubectl get namespaces
```

#### **Delete a Namespace:**
```sh
kubectl delete namespace app1-ns
```
**Warning:** Deleting a namespace **removes all resources within it**, including **pods**, **services**, **configmaps**, **secrets etc**..

---

### **Using Namespace Flags**

| **Flag** | **Description** |
|----------|-----------------|
| `-n <namespace-name>` or `--namespace` | Execute commands within a **specific namespace**. |
| `-A` or `--all-namespaces` | Execute commands across **all namespaces**. |

```sh
kubectl get pods -n app1-ns
kubectl get services -A
```

---

## **Deploying Frontend and Backend in a Namespace**

- We'll use **existing YAML files** for our **frontend** and **backend deployments**.
- Deploy the **frontend** and **backend** components in the **app1-ns** namespace.

---

### **1. Applying Frontend and Backend YAMLs**

#### **1.1 Frontend YAML (`frontend-deploy.yaml`)**
```sh
kubectl apply -f frontend-deploy.yaml -n app1-ns
```

#### **1.2 Backend YAML (`backend-deploy.yaml`)**
```sh
kubectl apply -f backend-deploy.yaml -n app1-ns
```

---

### **2. Verify the Deployments in `app1-ns`**

```sh
kubectl get all -n app1-ns
```

---

## **Testing Namespace Isolation**

### **1. Test Pod in `default` Namespace**
```sh
kubectl run test-pod --image=busybox -it --rm --restart=Never -- /bin/sh
```

```sh
curl backend-svc:9090 # ❌ Will not work
```
**For cross-namespace access, use the following format:**  
```sh
curl http://backend-svc.app1-ns:9090
```

### **Format:**  
```sh
curl http://<service-name>.<namespace-name>:<service-port>
```

- **`<service-name>`**: Name of the **Kubernetes Service**, e.g., **`backend-svc`**.  
- **`<namespace-name>`**: Namespace where the **service** is deployed, e.g., **`app1-ns`**.  
- **`<service-port>`**: The **ClusterIP port** exposed by the **service**, e.g., **`9090`**.  

---

### **2. Test Pod in `app1-ns` Namespace**
```sh
kubectl run test-pod -n app1-ns --image=busybox -it --rm --restart=Never -- /bin/sh
```

```sh
curl backend-svc:9090 # ✅ Should work
```

---

## **Setting a Default Namespace in Kubernetes Context**

### **Why?**  
It’s **cumbersome** to use `-n <namespace>` with **every command**. You can set a **default namespace** in the **Kubernetes context**.

```sh
kubectl config set-context --current --namespace=app1-ns
```

- Now, you **don't need** to use `-n app1-ns` with **every command**.  
- To **check the current context**, run:  

```sh
kubectl config get-contexts
```

---

## **Best Practices for Using Namespaces**

- **Segregate Workloads:** Separate **dev**, **test**, and **prod environments**.  
- **Use Namespaces for Multi-Tenancy:** Avoid **resource conflicts** by **isolating teams or projects**.  
- **Resource Quotas:** Set **limits** on **CPU**, **memory**, and **storage** per namespace.  
- **Namespace Naming Conventions:** Use **clear** and **consistent names** (e.g., `team-app-env` → `frontend-prod-ns`).  
- **Avoid Manual Deletion:** Use `kubectl delete namespace` **carefully**, as it **removes all resources within**.  
- **Apply Network Policies:** Secure namespaces using **network policies** to control **traffic flow**.  

---

## **Namespaces: Key Pointers**

- **Namespaces** provide **logical isolation** in Kubernetes.  
- They help with **security**, **resource management**, and **multi-tenancy**.  
- Use **imperative** and **declarative methods** to **create and manage namespaces**.  
- Be **careful when deleting namespaces**, as it **removes all resources within**.  
- **Set default namespaces** in your **Kubernetes context** for **ease of use**.  
- Follow **best practices** to **organize resources effectively** and **ensure security**.  

---


