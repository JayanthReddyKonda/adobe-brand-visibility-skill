import os
import shutil
import zipfile

def build():
    # 1. Clean output directory
    out_dir = "build/brand-ai-readiness-audit"
    if os.path.exists("build"):
        shutil.rmtree("build")
    
    os.makedirs(f"{out_dir}/skills", exist_ok=True)
    
    # 2. Copy root files
    for f in ["brand-ai-readiness-audit/marketplace.json", "brand-ai-readiness-audit/README.md", "brand-ai-readiness-audit/LICENSE"]:
        if os.path.exists(f):
            shutil.copy(f, out_dir)
            
    # 3. Process each skill
    skills = ["audit-orchestrator", "discoverability-audit", "entity-content-audit", 
              "fact-consistency-audit", "corroboration-authority-audit", 
              "geo-content-audit", "engagement-context-audit"]
              
    for skill in skills:
        skill_in = f"src/skills/{skill}"
        skill_out = f"{out_dir}/skills/{skill}"
        
        # Copy standard agentskills.io contents
        if os.path.exists(skill_in):
            shutil.copytree(skill_in, skill_out)
        
        # Bundle Core Library into the skill's scripts/ directory to make it self-contained
        os.makedirs(f"{skill_out}/scripts", exist_ok=True)
        for core_file in ["fetcher.py", "telemetry.py", "dom.py"]:
            if os.path.exists(f"src/core/{core_file}"):
                shutil.copy(f"src/core/{core_file}", f"{skill_out}/scripts/{core_file}")
                
    # 4. Create ZIP
    shutil.make_archive("brand-ai-readiness-audit", "zip", "build", "brand-ai-readiness-audit")
    print("Successfully built brand-ai-readiness-audit.zip")

if __name__ == "__main__":
    build()
