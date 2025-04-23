## Future Improvements & Recommendations

1. **Benchmarking on RAG (recall, accuracy, time taken etc.)**  
* Our group got the baseline product working, but unforeseen circumstances like migrating to the rag 2.0 repo slowed our progress towards the end and cut into benchmarking time  
2. **Test out different models for the tech stack**  
* For example, we are currently using snowflake embedding model, but NVIDIA’s llama3.2nvembed may be better  
* It would also be good to have benchmarks on these separate models  
3. **Multi-user deployment**  
* Due to time constraints, and constraints with the current RAG system as it sits April 2025, multiple users cannot chat and work with the same centralized deployment. We have been told this will be addressed soon, but is out of the scope of the project for the semester.  
* The current custom frontend developed by us will likely need to be updated to use a unique collection in the knowledge base for each canvas access token, so that users have an individualized experience when chatting with the same centralized knowledge base.   
* Piloting with two future classes for the Fall Semester according to Professor Russell  
* (**NOTE:** NVIDIA may modify how a centralized deployment works in the future and even add docs for it, this is just an educated guess in the current system)  
4. **Text to Speech and Speech to Text overhaul**  
* For our team, relying on browser accessibility was a nightmare. In theory, it was easy because it was built in and so would be a quick nice to have feature. In reality, browsers love to always do it differently  
* Our recommendation would be to use a separate model which would likely perform better and work across all systems, with the obvious choice for this project being NVIDIA Riva for speech.   
5. **Implement more guardrails files and features**   
* Guardrails are modular by nature so adding guardrails files and rails would be very easy to implement based on the end user’s needs.  
6. **Set up helm chart deployment**  
* Due to time constraints, we were unable to fully convert from a docker compose set up to an K8s deployment. Current options for deployment are through compose and a brev launchable notebook.  
* Future work would definitely be possible through microk8s setup