## Limitations

1. **Untested with multiple users:**  
* Our code has only been tested with one machine, running one frontend. If multiple people access the frontend, they can all chat, but will all share the same vector database, which can cause issues. We have not had access to any centralized deployment for testing.  
  * For a potential solution, utilizing collections that give each unique canvas token its own collection will probably work, we just did not think about this in design and did not have time to test to figure it out.

* Limitations with nvidia microservices itself, someone from nv-ingest team mentioned that there may be some limitations like if one user uploads one thousand files first and someone else uploaded one file after that they would have to wait for the subsequent one thousand files to finish uploading first.	

    This means that an institution running it for a full class of students is probably not going to work, and it can only be used as a beta in an individualized context.

2. **If an instructor decides not to have a files tab or course structure, the tabs will be blank on our frontend**  
* One thing that can be frustrating as a student is that often times professors will have their own completely different way of utilizing canvas, and that can sometimes be very improper. Because our course download grabs course structure and files, if an instructor adds no files or has no structure it will not show.   
* With all our testing, it seemed to be only the case that there were not any files, but there was always structure. Due to this, we did add a message that tells the user “Files seem empty, try clicking course structure” to keep the system usable. We did not have an example of neither course structure nor files, and educated guess says that in that case the product will not work  
* (**NOTE:** if an instructor has no structure or files, this is more likely an issue with that instructor and their usage of canvas than it is with our product)   
3. **Personas only work with guardrails off:**   
* Injecting the persona into the user prompt the way that we do allows for really easy bypass of the guardrails, and when the guardrails trigger, the python actions do not follow the persona for the response.  
  * Due to the nature of the personas, the persona is injected through the user prompt and this bypasses the guardrails.  
4. **Speech to Text Accessibility does not work on all browsers:**  
* Using speech to text works on chrome provided it has proper mic access, but does not work on other browsers like firefox. Additionally, getting the proper mic access to the browser seems to be difficult.  
  * Future updates could possibly use NVIDIA Riva as a model for speech to text, would allow for easy expansion to text to speech too.   
5. **Guardrails do not support streaming:**  
* The response gets streamed for a more fluid output in the chat, and this does not work with the guardrails on, it will not stream with the rails on. This could be as simple as a setting somewhere, we just did not find it.  
  * Not built in, but definitely possible to implement for future works   
6. **Guardrails microservice needs to be restarted on docker to run and the end user may need to manually pip install on their local machine.**  
* **pip install langchain-nvidia-ai-endpoints**  
* **pip install langchain-unstructured**


