### **Lecture 2: Docker Installation, Image Lifecycle, Port Forwarding, Exec vs Shell form**

---

#### **1. Installing Docker**

You can install Docker in one of two ways depending on your setup:

**Option 1: Docker Desktop (Recommended for local development)**

* Ideal if your laptop has sufficient resources (at least 8GB RAM recommended).
* Installation link: [Get Docker Desktop](https://docs.docker.com/get-started/get-docker/)

**Option 2: Docker Engine on a VM**

* Suitable for those using a cloud VM (e.g. AWS EC2 or GCP Compute Engine).
* Follow this guide for Ubuntu-based systems: [Install Docker Engine on Ubuntu](https://docs.docker.com/engine/install/ubuntu/)

To verify your installation:

```bash
docker --version    # Succinct version info
docker version      # Detailed version info
```
---

### **Installation on macOS, Windows, and Linux**

![Alt text](/images/2d.png)

Docker behaves differently depending on the operating system because containers require a Linux kernel. Here's how storage is handled across platforms:

#### **Linux**

- On **Linux**, Docker runs **natively** without any virtualization layer.

---

#### **macOS and Windows**

Docker does **not** run natively on macOS or Windows. Instead, **Docker Desktop** provides a Linux environment using a lightweight virtual machine.

| OS        | Virtualization Backend                         |
|-----------|------------------------------------------------|
| macOS     | Docker Desktop uses a Linux VM via the **Apple Virtualization Framework** (previously **HyperKit**) |
| Windows   | Docker Desktop uses **WSL 2 (Windows Subsystem for Linux)** to run the Linux kernel |

**Can You Install Docker Engine Directly on macOS or Windows?**

❌ **No, not directly like on Linux.**
- Both **macOS** and **Windows** do **not have a native Linux kernel**, which Docker Engine **requires** to run containers.
- Docker Engine relies heavily on Linux features like **cgroups**, **namespaces**, and **UnionFS (e.g., overlay2)** — which are unavailable on macOS and Windows.
     
    - **cgroups** are a Linux kernel feature that limit and isolate the resource usage (CPU, memory, disk I/O, etc.) of a group of processes.
    - **Namespaces** provide process-level isolation by creating separate views of system resources like PID, network, mount, and filesystem. This allows containers to run as if they are the only process on the system.


**NOTE**: While you can install **Docker Desktop** on a **Linux system**, it’s generally not recommended because Linux natively supports Docker Engine, which is more lightweight and efficient. When you run Docker Desktop on Linux, it still creates a lightweight virtual machine using the system's virtualization technology, adding an unnecessary layer of overhead compared to using Docker Engine directly on the host.

---

### **2. Understanding Container Registries, Repositories, and Images**

* A **Container Registry** is a storage and distribution system for container images.
  Common examples:

  * **Public registries**: Docker Hub, GitHub Container Registry
  * **Cloud-native registries**: Amazon ECR, Google Artifact Registry, Azure Container Registry


* A **Repository** is a namespace or collection of related images in a registry.
  Repositories group different **versions (tags)** of the same base image.

  **Example:** The `ubuntu` repository in Docker Hub includes:

  * `ubuntu:20.04`
  * `ubuntu:22.04`
  * `ubuntu:latest`


* An **Image** is a specific, versioned snapshot of a containerized application or environment.
  It includes the OS layer, binaries, dependencies, and runtime configuration. The **image** is the actual binary artifact, and the **tag** identifies a specific version within a repository.

  An image is typically identified as:

  ```
  <registry>/<repository>:<tag>
  ```

  **Example:**
  `docker.io/ubuntu:22.04`

  * Registry: Docker Hub
  * Repository: `ubuntu`
  * Tag: `22.04`
  * This refers to a specific version (22.04) of the `ubuntu` image.

---

> ⚠️ **Don’t confuse container repositories with Git repositories**
>
> A **container repository** stores **built container images**, not source code.
> It's where tools like Docker or Kubernetes pull **runnable artifacts** from.
>
> A **Git repository**, on the other hand, stores **source code**, configuration files, or infrastructure-as-code — not compiled images.
>
> Example:
>
> * GitHub repo: `github.com/myorg/flask-app` → contains code
> * Container repo: `ghcr.io/myorg/flask-app:1.0` → contains the built image

---

> **Note**: You'll often hear terms like *Docker images* or *Docker containers*. This terminology is widespread because **Docker** was the first and most popular tool to build and run containers. However, the correct and more neutral term is **container images**, especially as the industry increasingly adopts the **OCI (Open Container Initiative)** standard.
>
> While Docker is still widely used, it's not the only tool for building container images. Other tools include:
>
> * **Podman**: A daemonless, Docker-compatible tool that's OCI-compliant and works without root access.
> * **Buildah**: Focuses on building OCI images with fine-grained control and is often used in automation pipelines.
> * **Kaniko**: Allows building container images in Kubernetes or other containerized environments without requiring privileged access.
> * **img**: A secure, daemonless builder for container images, designed to work in CI environments.
> * **Jib** (for Java): Builds optimized container images for Java applications without needing a Dockerfile or Docker daemon.
> * **ko** (for Go): Builds and pushes Go applications as OCI-compliant container images without writing Dockerfiles.
>
> These tools support modern use cases such as rootless builds, improved security, and integration into CI/CD pipelines without relying on the Docker daemon.


---

### **3. Running Basic Docker Commands**

Let’s use the Docker CLI to explore some core commands that help you interact with container images.

> **Tip**: Don’t hesitate to use help flags — they’re highly informative and guide you through CLI usage.

```bash
docker --help
docker pull --help
```

---

#### **Example 1: Pulling a Base Image**

![Alt text](/images/2a.png)

**Syntax:**

```bash
docker pull <registry>/<namespace>/<repository>:<tag>
```

**Default (shorthand) usage:**

```bash
docker pull ubuntu
```

This is equivalent to:

```bash
docker pull ubuntu:latest
```

And fully qualified as:

```bash
docker pull docker.io/library/ubuntu:latest
```

Let’s break it down:

* `docker.io` – The **registry**, which in this case is Docker Hub.
* `library` – The **namespace**, used for official images maintained by Docker (e.g., `ubuntu`, `nginx`, `alpine`).

  * Think of a **namespace** as a logical grouping of repositories, usually representing a user or organization.
* `ubuntu` – The **repository**, which holds different versions (tags) of the Ubuntu image.
* `latest` – The **tag**, referring to the most recently pushed version with this label.

  * Important: `latest` doesn’t always mean the most recent version — just the one explicitly tagged as `latest` during push.

---

#### **Namespaces in Docker Registries**

* A **namespace** helps organize repositories, typically by user or organization.

  * For example:
    `docker.io/varunjoshi0404/my-first-image:v1.0`
    Here, `varunjoshi0404` is the **namespace** and `my-first-image` is the **repository**.

---


**Common Container Image Pull Syntax and Examples**

**Docker Hub (Private):**
`docker pull docker.io/<username>/<image-name>:<tag>`
Example: `docker pull docker.io/varunjoshi0404/my-first-image:v1.0`

**Note:**  In Docker Hub, the part right after the registry (docker.io)—like `<username>` or `<organization>` —is called the namespace.

---

**AWS ECR:**
`docker pull <account-id>.dkr.ecr.<region>.amazonaws.com/<image-name>:<tag>`
Example: `docker pull 123456789012.dkr.ecr.us-east-1.amazonaws.com/my-app:v1.0`

---

**GCR (Google Container Registry):**
`docker pull gcr.io/<project-id>/<image-name>:<tag>`
Example: `docker pull gcr.io/my-gcp-project/my-app:v1.0`

---

**GCP Artifact Registry:**
`docker pull <region>-docker.pkg.dev/<project-id>/<repo-name>/<image-name>:<tag>`
Example: `docker pull us-central1-docker.pkg.dev/my-gcp-project/my-repo/my-app:v1.0`

---

#### **4. Creating Your First Container Image**

Let’s walk through creating a custom container image using a Dockerfile.

---

### **Step 1: Create a `Dockerfile`**

```Dockerfile
FROM ubuntu:latest
CMD echo "Hello, Docker!"
```

* `FROM ubuntu:latest`: Uses the latest Ubuntu image as the base layer.
* `CMD echo "Hello, Docker!"`: Sets the default command to run when a container starts.

---

### **Step 2: Build the Image**

**Syntax:**

```bash
docker build -t <image-name> <build-context>
```

**Example:**

```bash
docker build -t my-first-image .
```

**Explanation:**

When you run:

```bash
docker build -t my-first-image .
```

* `-t my-first-image`:
  Shorthand for `--tag`. It assigns a **name** (and optionally a **tag**) to the resulting image.
  In this case:

  * Image name: `my-first-image`
  * Tag: Defaults to `latest` if not specified, so it becomes `my-first-image:latest`

  > You can also explicitly tag with a version like `-t my-first-image:v1`.
* `.` (dot):

  * Represents the **current directory** (`$PWD`).
  * It tells Docker to use this directory as the **build context**.
  * **All contents** of this directory — including files and subdirectories — are **archived and sent** to the Docker daemon.

This is why large contexts (with unnecessary files) can **slow down builds** or **accidentally expose secrets** if you're not careful.

---

**What’s in the Build Context?**

* Docker copies everything inside the directory passed as the context (`.` in this case).
* Then it uses the `Dockerfile` (usually in the same dir unless specified with `-f`) and any referenced files (e.g., `COPY ./app /app`) from **within that context only**.

**Pro Tip:** Add `.dockerignore`

To avoid sending sensitive or irrelevant files, create a `.dockerignore`:

```dockerignore
.git
node_modules
.env
*.log
```

This works just like `.gitignore` and improves security + performance.

> **Note:** Only include files necessary for building the image in the build context. Keeping unwanted files (like logs, large binaries, or source directories not used in the Dockerfile) can unnecessarily load the machine performing the build, increase context upload time, and slow down the overall build process. Use a `.dockerignore` file to exclude such files and keep builds efficient.


---

**Using Custom Dockerfiles (e.g., Dockerfile-prod, Dockerfile-dev)**

In real-world projects, it's common to maintain **multiple Dockerfiles** tailored for different environments such as development, staging, or production. This allows for environment-specific dependencies, optimizations, and configurations without modifying the main Dockerfile repeatedly.

Examples:

* `Dockerfile-dev`: includes debug tools, live-reload, volume mounts
* `Dockerfile-prod`: optimized for performance, minimal layers, no dev dependencies
* `Dockerfile-staging`: similar to prod but may include staging-specific variables or labels

Instead of naming every file `Dockerfile`, you can reference a custom file using the `-f` flag with `docker build`.

**Build Syntax:**

```bash
docker build -t <image-name> -f <path-to-custom-dockerfile> <build-context>
```

**Example:**

```bash
docker build -t flask-api:prod -f Dockerfile-prod .
docker build -t flask-api:dev -f ./docker/Dockerfile-dev .
```

This keeps your builds clean and tailored, while maintaining clear separation of concerns per environment.

---

**Dockerfile Instructions and Image Layers**

Docker builds images in **layers**, and not all instructions contribute a new layer. Here's the corrected categorization:

#### **Layer-Creating Instructions**

These create a new filesystem layer:

```
FROM, RUN, COPY, ADD
```

#### **Non-Layer-Creating Instructions**

These only update image metadata and do **not** create new layers:

```
CMD, ENTRYPOINT, ENV, ARG, LABEL, EXPOSE, VOLUME, USER, WORKDIR, STOPSIGNAL, HEALTHCHECK, SHELL
```

> **Note**: `ENV`, `ARG`, `LABEL`, etc., do *not* modify the filesystem. So while they affect image metadata, they do not generate a new filesystem layer unless combined with a filesystem-modifying command.

---


#### **5. Running and Managing Containers**

Let’s explore how to run and manage containers using Docker CLI.

---

**Syntax to run a container:**

```bash
docker run [OPTIONS] <image-name>
```

**Example:**

```bash
docker run --name my-first-cont my-first-image
```

*This runs a new container from the `my-first-image`, and names it `my-first-cont`.*

---

**Syntax to list only running containers:**

```bash
docker ps
```

*Shows currently running containers, including container ID, name, image, status, ports, and more.*


> **Note:**
> Unlike virtual machines, containers are designed to be lightweight and ephemeral. They are expected to **exit once their task is complete**. For example:
>
> * A container serving a website or API will run continuously.
> * But a container that copies a file from location A to B, processes a batch of data, or prints a message is meant to **run briefly and then exit**.
>
> That’s why our `my-first-cont` container appears in an **Exited** state — it simply printed `"Hello, Docker!"` as instructed and then stopped, having completed its job.



---

**Syntax to list all containers (running + stopped):**

```bash
docker ps -a
```

*Useful to inspect containers that have exited or failed.*


---


#### **6. Pushing an Image to Docker Hub**

**Step 1: Tag the image**
Syntax:

```bash
docker tag <local-image> <namespace>/<image>:<tag>
```

Example:

```bash
docker tag my-first-image varunjoshi0404/my-first-image:v1.0
```

> **Note 1:** You don’t specify the Docker Hub account separately when pushing. Tagging the image with your Docker Hub username (namespace) ensures it is pushed to the correct repository.



> **Note 2:**
> When you run a command like:
>
> ```bash
> docker tag my-first-image varunjoshi0404/my-first-image:v1.0
> ```
>
> Docker interprets `varunjoshi0404/my-first-image:v1.0` as a reference to a repository on Docker Hub.
> If no registry is specified (like `ghcr.io` or `gcr.io`), **Docker automatically prefixes it with `docker.io`**, the default Docker Hub registry.
>
> So the full image reference becomes:
>
> ```
> docker.io/varunjoshi0404/my-first-image:v1.0
> ```

---


**Step 2: Push the image**
Syntax:

```bash
docker push <namespace>/<image>:<tag>
```

Example:

```bash
docker push varunjoshi0404/my-first-image:v1.0
```

Docker automatically prefixes `docker.io` if omitted:

```bash
docker push docker.io/<namespace>/<image>:<tag>
```
**Note**:
If you're using **Docker Desktop**, you might not be prompted for credentials because you're already logged in through the GUI.

For users on an **Ubuntu VM** or other CLI-only environments, you can log in using:

```bash
docker login
```

---

### **Running an Nginx Container (Foreground vs Detached Mode)**

When you run the following command:

```bash
docker run nginx
```

The **Nginx process takes over your terminal**. This is because the default command runs in the **foreground**, meaning the container’s standard output is attached to your terminal.

> This behavior is expected for long-running processes like web servers, but it's rarely desirable in interactive sessions — especially when you want to keep the service running while continuing to use the terminal.

You can confirm the container is running by opening a new terminal and executing:

```bash
docker ps
```

Now, if you press `Ctrl+C` in the original terminal, the container receives a termination signal and stops. It will **no longer appear in `docker ps` output**.

---

### **Running in Detached Mode with Port Mapping**

![Alt text](/images/2b.png)

Let’s run the same Nginx container properly — in the background, with named identification and accessible over HTTP:

```bash
docker run -d -p 8080:80 --name my-nginx-cont nginx
```

**Breakdown of flags:**

* **`-d` (Detached Mode):**
  Runs the container in the background, freeing up your terminal.

* **`-p 8080:80` (Port Mapping):**
  Maps **port 80** in the container (where Nginx listens by default) to **port 8080** on your **host machine**.

* **`--name my-nginx-cont`:**
  Assigns a custom name to the container for easier tracking and management.

After running this command, open your browser and go to:

```
http://localhost:8080
```

You should see the **default Nginx welcome page**.

---

### **Tip: Understanding Port Mapping (`-p hostPort:containerPort`)**

A useful way to remember the order:

> **Traffic comes from outside → hits the host → then forwarded to the container.**

So the syntax is always:

```
docker run -p <hostPort>:<containerPort>
```

In our case:

```bash
-p 8080:80
```

Means:

* **8080** on the host is forwarded to
* **80** inside the container (where Nginx listens)

> Note: Once a host port like **8080** is mapped to a container, it’s **reserved** — you can’t reuse it for another container or service unless you stop the existing one.

---

## Containerizing a Python Flask App with Docker

---

### Dockerfile Instructions and Their Purpose (Syntax First)

| **Instruction** | **Syntax**                                        | **Purpose**                                                                                 | **Example**                                      |
| --------------- | ------------------------------------------------- | ------------------------------------------------------------------------------------------- | ------------------------------------------------ |
| **FROM**        | `FROM <base-image>`                               | Sets the base image for building your application. Required as the first instruction.       | `FROM ubuntu:latest`                             |
| **LABEL**       | `LABEL <key>=<value>`                             | Adds metadata to the image (e.g., maintainer, version).                                     | `LABEL maintainer="varun@example.com"`           |
| **ENV**         | `ENV <key>=<value>`                               | Sets environment variables for the image and future instructions.                           | `ENV PORT=5000`                                  |
| **ADD**         | `ADD <src> <dest>`                                | Copies files and auto-extracts archives or fetches from URLs. Use only when needed.         | `ADD app.tar.gz /app`                            |
| **COPY**        | `COPY <src> <dest>`                               | Copies local files or directories. Preferred over `ADD` for basic use.                      | `COPY app.py /app/app.py`                        |
| **RUN**         | `RUN <command>`                                   | Executes commands during build, typically to install dependencies.                          | `RUN apt-get update && apt-get install -y nginx` |
| **WORKDIR**     | `WORKDIR <path>`                                  | Sets the working directory for future instructions.                                         | `WORKDIR /app`                                   |
| **EXPOSE**      | `EXPOSE <port>`                                   | Documents which port the container listens on. Requires `-p` during `docker run` to expose. | `EXPOSE 5000`                                    |
| **CMD**         | `CMD ["executable", "param1"]` or `CMD <command>` | Sets the default command to run when the container starts. Overridden by `docker run`.      | `CMD ["python", "app.py"]`                       |
| **ENTRYPOINT**  | `ENTRYPOINT ["executable", "param1"]`             | Sets a fixed command that always runs. Use `--entrypoint` to override at runtime.           | `ENTRYPOINT ["nginx", "-g", "daemon off;"]`      |

---

> 💡 **Less Common Instructions**
> Advanced instructions like `ARG`, `VOLUME`, `USER`, `HEALTHCHECK`, `STOPSIGNAL`, `ONBUILD`, and `SHELL` are also available and useful in more complex Dockerfiles. It's a good idea to be aware of them as your Docker usage matures. Let me know if you’d like a separate table for those as well.


> Note: Use COPY when you simply want to move files. Use ADD only when you need archive extraction or remote URL download.

---

### About the Flask Framework

**Flask** is a lightweight web framework for Python that enables you to build web servers and APIs with minimal boilerplate. It's popular for its simplicity and flexibility, especially in containerized environments.

---

### Sample Flask Application Code

```python
from flask import Flask

app = Flask(__name__)

@app.route("/")
def home():
    return "Hello, Docker!"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
```

**Explanation:**

* `Flask(__name__)`: Initializes the Flask app.
* `@app.route("/")`: Sets up a route for the root URL.
* `app.run(...)`: Runs the web server, listening on all interfaces (0.0.0.0) and port 5000.

---

### Dockerfile to Containerize the Flask App

```Dockerfile
# Use a lightweight Python image as the base
FROM python:3.9-slim

# Set the working directory inside the container
WORKDIR /app

# Copy the application file from the host to the container
COPY app.py /app/app.py

# Install Flask library
RUN pip install flask

# Expose the port where the app will run
EXPOSE 5000

# Default command to run the application
CMD ["python", "app.py"]
```

---

### Building and Running the Container

**Step 1: Build the image**

```bash
docker build -t my-python-image .
```

**Step 2: Tag the image for Docker Hub**

```bash
docker tag my-python-image varunjoshi0404/my-python-image:v1.0
```

> **Note:**
> Instead of running the build and tag commands separately:
>
> ```bash
> docker build -t my-python-image .
> docker tag my-python-image varunjoshi0404/my-python-image:v1.0
> ```
>
> You can directly build and tag the image for Docker Hub in one step:
>
> ```bash
> docker build -t varunjoshi0404/my-python-image:v1.0 .
> ```
>
> This saves time and avoids an extra command.


**Step 3: Push the image**

```bash
docker push varunjoshi0404/my-python-image:v1.0
```

**Step 4: Run the container**

```bash
docker run -d -p 8082:5000 --name=my-python-container varunjoshi0404/my-python-image:v1
```

**Step 5: Verify**
Open browser: `http://localhost:8082`

---


### CMD: Exec Form vs Shell Form

![Alt text](/images/2c.png)

| **Aspect**           | **Exec Form** (`CMD ["python", "app.py"]`)     | **Shell Form** (`CMD python app.py`)                    |
| -------------------- | ---------------------------------------------- | ------------------------------------------------------- |
| **Syntax**           | JSON array format                              | Plain string interpreted by shell (`/bin/sh -c`)        |
| **Process (PID 1)**  | App (e.g., `python`) runs directly as PID 1    | Shell runs as PID 1; app is a child process             |
| **Signal Handling**  | Signals go directly to app (clean shutdown)    | Signals go to shell; app may not receive them           |
| **Variable support** | No shell variable expansion (literal only)     | Supports environment variable expansion                 |
| **Error behavior**   | Errors in commands are explicit and visible    | Shell handles errors unless `set -e` is used            |
| **Best for**         | Production containers (more reliable, clearer) | Quick scripts, debugging, or when shell logic is needed |

---

> **Recommendation:**
> In Dockerfiles, prefer using the **exec form** (`["executable", "arg1", "arg2"]`) in production environments. It ensures proper signal handling, better compatibility with container orchestrators like Kubernetes, and avoids unexpected shell parsing issues. Use the **shell form** (`RUN command && command2`) only when you explicitly need shell features such as command chaining (`&&`), piping (`|`), redirection (`>`), or variable expansion (`$VAR`). The exec form provides more predictable, safer behavior, especially for long-running processes. Use shell form judiciously, typically for setup tasks or scripts that require shell logic.
---

### Demonstrating Shell Form

**Modify Dockerfile CMD**

```Dockerfile
CMD python app.py
```

**Rebuild the image**

```bash
docker build -t shell-form-image .
```

**Run the container**

```bash
docker run -d -p 8082:5000 --name=shell-form-container shell-form-image
```

**Compare running processes**

```bash
docker top my-python-container

docker top shell-form-container
```

> You will see that in the shell-form container, the `sh` process wraps your `python` command, while in the exec-form container, `python` is directly PID 1.

---

### **Wrapping Up: Troubleshooting & Cleanup Essentials**

#### **Run Commands Inside a Container**

```bash
docker exec -it <container> <cmd>      # Example: docker exec -it my-python-container bash
```

* Interactive shell access to running containers
* `-i`: Keep STDIN open, `-t`: Allocate pseudo-TTY

#### **View Container Logs**

```bash
docker logs <container>                # Example: docker logs my-python-container
```

* View application output or debug behavior

---

### **Cleanup Commands**

#### **Delete Image**

```bash
docker rmi <image>                     # Example: docker rmi my-python-image
```

* Fails if container is using the image

#### **Delete Container**

```bash
docker rm <container>                 # Example: docker rm my-python-container
```

* Stop it first: `docker stop <container>`

---

### **Other Handy Commands**

| Purpose                         | Command                                 |
| ------------------------------- | --------------------------------------- |
| List all containers             | `docker ps -a`                          |
| Inspect container/image         | `docker inspect <id>`                   |
| View processes inside container | `docker top <container>`                |
| Stop/start/restart container    | `docker stop/start/restart <container>` |
| Stop all running containers     | `docker stop $(docker ps -q)`           |
| Delete all stopped containers   | `docker container prune`                |
| Delete specific image           | `docker rmi <image>`                    |
| Remove all unused images        | `docker image prune -a`                 |

> ⚠️ *Dangling images*: Unused images with no tag; safe to remove using `docker image prune -a`

---