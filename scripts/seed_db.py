#!/usr/bin/env python3
"""
Seed script for Interim App Database
Populates the database with mock data for testing and development
"""

import sys
import os
from datetime import datetime, timedelta
import random

# Add the app directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from app import create_app
from app.models.user import User
from app.models.company import Company
from app.models.job import Job
from app.models.application import Application

def create_mock_users():
    """Create mock users"""
    users_data = [
        {
            "email": "jean.dupont@email.com",
            "password": "password123",
            "nom": "Dupont",
            "prenom": "Jean",
            "telephone": "0123456789",
            "competences": ["Python", "Flask", "JavaScript", "React"],
            "experience": "3 ans d'expérience en développement web full-stack"
        },
        {
            "email": "marie.martin@email.com", 
            "password": "password123",
            "nom": "Martin",
            "prenom": "Marie",
            "telephone": "0123456790",
            "competences": ["Java", "Spring", "Angular", "MySQL"],
            "experience": "5 ans d'expérience en développement backend"
        },
        {
            "email": "pierre.durand@email.com",
            "password": "password123", 
            "nom": "Durand",
            "prenom": "Pierre",
            "telephone": "0123456791",
            "competences": ["React", "Node.js", "MongoDB", "Docker"],
            "experience": "2 ans d'expérience en développement moderne"
        },
        {
            "email": "sophie.bernard@email.com",
            "password": "password123",
            "nom": "Bernard", 
            "prenom": "Sophie",
            "telephone": "0123456792",
            "competences": ["PHP", "Laravel", "Vue.js", "PostgreSQL"],
            "experience": "4 ans d'expérience en développement web"
        },
        {
            "email": "lucas.petit@email.com",
            "password": "password123",
            "nom": "Petit",
            "prenom": "Lucas", 
            "telephone": "0123456793",
            "competences": ["C#", ".NET", "Azure", "SQL Server"],
            "experience": "6 ans d'expérience en développement Microsoft"
        }
    ]
    
    created_users = []
    print("🧑‍💼 Creating users...")
    
    for user_data in users_data:
        try:
            user = User(**user_data)
            user_id = user.save()
            if user_id:
                created_users.append(str(user_id))
                print(f"   ✅ Created user: {user_data['prenom']} {user_data['nom']}")
            else:
                print(f"   ❌ Failed to create user: {user_data['email']}")
        except Exception as e:
            print(f"   ⚠️  User {user_data['email']} might already exist: {str(e)}")
    
    return created_users

def create_mock_companies():
    """Create mock companies"""
    companies_data = [
        {
            "email": "contact@techcorp.fr",
            "password": "password123",
            "nom": "TechCorp Solutions",
            "description": "Leader en solutions technologiques innovantes",
            "secteur": "Informatique",
            "adresse": "123 Avenue des Champs-Élysées, 75008 Paris",
            "telephone": "0140123456",
            "site_web": "https://www.techcorp.fr"
        },
        {
            "email": "rh@digitalnova.fr",
            "password": "password123", 
            "nom": "Digital Nova",
            "description": "Agence digitale spécialisée en transformation numérique",
            "secteur": "Services numériques",
            "adresse": "45 Rue de la République, 69002 Lyon",
            "telephone": "0472123456",
            "site_web": "https://www.digitalnova.fr"
        },
        {
            "email": "jobs@startuplab.fr",
            "password": "password123",
            "nom": "StartupLab",
            "description": "Incubateur de startups technologiques",
            "secteur": "Innovation",
            "adresse": "78 Boulevard Saint-Germain, 75005 Paris", 
            "telephone": "0145123456",
            "site_web": "https://www.startuplab.fr"
        },
        {
            "email": "recrutement@webagency.fr",
            "password": "password123",
            "nom": "WebAgency Pro",
            "description": "Agence web créative et performante",
            "secteur": "Communication",
            "adresse": "12 Place Bellecour, 69002 Lyon",
            "telephone": "0478123456", 
            "site_web": "https://www.webagency.fr"
        },
        {
            "email": "hr@futuretech.fr",
            "password": "password123",
            "nom": "FutureTech Industries",
            "description": "Développement de solutions IoT et IA",
            "secteur": "Technologie",
            "adresse": "33 Cours Mirabeau, 13100 Aix-en-Provence",
            "telephone": "0442123456",
            "site_web": "https://www.futuretech.fr"
        }
    ]
    
    created_companies = []
    print("🏢 Creating companies...")
    
    for company_data in companies_data:
        try:
            company = Company(**company_data)
            company_id = company.save()
            if company_id:
                created_companies.append(str(company_id))
                print(f"   ✅ Created company: {company_data['nom']}")
            else:
                print(f"   ❌ Failed to create company: {company_data['nom']}")
        except Exception as e:
            print(f"   ⚠️  Company {company_data['email']} might already exist: {str(e)}")
    
    return created_companies

def create_mock_jobs(company_ids):
    """Create mock jobs for companies"""
    jobs_templates = [
        {
            "titre": "Développeur Full Stack React/Node.js",
            "description": "Rejoignez notre équipe pour développer des applications web modernes avec React et Node.js. Vous travaillerez sur des projets innovants dans un environnement agile.",
            "salaire": "40000-50000 EUR",
            "type_contrat": "CDI",
            "localisation": "Paris, France",
            "competences_requises": ["React", "Node.js", "MongoDB", "JavaScript", "Git"],
            "experience_requise": "2-4 ans d'expérience"
        },
        {
            "titre": "Développeur Backend Python/Django",
            "description": "Nous cherchons un développeur backend expérimenté pour concevoir et maintenir nos APIs. Maîtrise de Python et Django requise.",
            "salaire": "45000-55000 EUR", 
            "type_contrat": "CDI",
            "localisation": "Lyon, France",
            "competences_requises": ["Python", "Django", "PostgreSQL", "Docker", "REST API"],
            "experience_requise": "3-5 ans d'expérience"
        },
        {
            "titre": "Développeur Frontend Angular",
            "description": "Développez des interfaces utilisateur modernes et responsives avec Angular. Travail en équipe sur des projets clients variés.",
            "salaire": "38000-48000 EUR",
            "type_contrat": "CDD",
            "localisation": "Lille, France", 
            "competences_requises": ["Angular", "TypeScript", "SCSS", "RxJS"],
            "experience_requise": "2-3 ans d'expérience"
        },
        {
            "titre": "DevOps Engineer",
            "description": "Automatisez le déploiement et la gestion de notre infrastructure cloud. Expertise en Docker, Kubernetes et CI/CD requise.",
            "salaire": "50000-65000 EUR",
            "type_contrat": "CDI",
            "localisation": "Paris, France",
            "competences_requises": ["Docker", "Kubernetes", "AWS", "Jenkins", "Terraform"],
            "experience_requise": "4-6 ans d'expérience"
        },
        {
            "titre": "Développeur Mobile React Native",
            "description": "Créez des applications mobiles cross-platform avec React Native. Projets innovants dans le secteur fintech.",
            "salaire": "42000-52000 EUR",
            "type_contrat": "CDI", 
            "localisation": "Toulouse, France",
            "competences_requises": ["React Native", "JavaScript", "iOS", "Android"],
            "experience_requise": "2-4 ans d'expérience"
        },
        {
            "titre": "Data Scientist",
            "description": "Analysez et exploitez nos données pour créer des modèles prédictifs. Maîtrise de Python et Machine Learning essentielle.",
            "salaire": "48000-58000 EUR",
            "type_contrat": "CDI",
            "localisation": "Nice, France",
            "competences_requises": ["Python", "Pandas", "Scikit-learn", "TensorFlow", "SQL"],
            "experience_requise": "3-5 ans d'expérience"
        },
        {
            "titre": "Développeur PHP/Symfony",
            "description": "Maintenez et développez nos applications web avec PHP et Symfony. Environnement collaboratif et projets stimulants.",
            "salaire": "35000-45000 EUR",
            "type_contrat": "Interim",
            "localisation": "Bordeaux, France",
            "competences_requises": ["PHP", "Symfony", "MySQL", "Doctrine", "Twig"],
            "experience_requise": "2-4 ans d'expérience"
        },
        {
            "titre": "Tech Lead Frontend",
            "description": "Dirigez une équipe de développeurs frontend et définissez l'architecture technique. Leadership et expertise technique requis.",
            "salaire": "55000-70000 EUR",
            "type_contrat": "CDI",
            "localisation": "Paris, France",
            "competences_requises": ["React", "Vue.js", "Leadership", "Architecture", "Mentoring"],
            "experience_requise": "5+ ans d'expérience"
        }
    ]
    
    created_jobs = []
    print("💼 Creating jobs...")
    
    for i, job_template in enumerate(jobs_templates):
        try:
            # Assign job to a random company
            company_id = random.choice(company_ids)
            
            job = Job(
                company_id=company_id,
                **job_template
            )
            
            job_id = job.save()
            if job_id:
                created_jobs.append(str(job_id))
                print(f"   ✅ Created job: {job_template['titre']}")
            else:
                print(f"   ❌ Failed to create job: {job_template['titre']}")
        except Exception as e:
            print(f"   ❌ Error creating job {job_template['titre']}: {str(e)}")
    
    return created_jobs

def create_mock_applications(user_ids, job_ids, company_ids):
    """Create mock applications"""
    motivations = [
        "Je suis très intéressé par ce poste car il correspond parfaitement à mon profil et à mes ambitions professionnelles.",
        "Votre entreprise a une excellente réputation et je souhaiterais contribuer à vos projets innovants.",
        "Cette opportunité me permettrait de développer mes compétences dans un environnement stimulant.", 
        "Je suis passionné par les technologies que vous utilisez et j'aimerais rejoindre votre équipe.",
        "Mon expérience dans le domaine serait un atout pour votre entreprise et ce projet m'enthousiasme."
    ]
    
    created_applications = []
    print("📝 Creating applications...")
    
    # Create 15-20 random applications
    num_applications = random.randint(15, 20)
    
    for i in range(num_applications):
        try:
            user_id = random.choice(user_ids)
            job_id = random.choice(job_ids)
            
            # Find the company for this job
            job = Job.find_by_id(job_id)
            if not job:
                continue
                
            company_id = job.company_id
            
            # Check if application already exists
            if Application.check_existing_application(user_id, job_id):
                continue
            
            application = Application(
                user_id=user_id,
                job_id=job_id,
                company_id=company_id,
                lettre_motivation=random.choice(motivations)
            )
            
            application_id = application.save()
            if application_id:
                created_applications.append(str(application_id))
                
                # Randomly update some application statuses
                if random.random() < 0.3:  # 30% chance
                    status = random.choice(["Acceptée", "Refusée"])
                    application.update_status(application_id, status)
                    print(f"   ✅ Created application with status: {status}")
                else:
                    print(f"   ✅ Created application: En attente")
            else:
                print(f"   ❌ Failed to create application")
                
        except Exception as e:
            print(f"   ❌ Error creating application: {str(e)}")
    
    return created_applications

def main():
    """Main seeding function"""
    print("🌱 Starting database seeding...")
    print("=" * 50)
    
    # Create Flask app context
    app = create_app()
    
    with app.app_context():
        try:
            # Create mock data
            user_ids = create_mock_users()
            company_ids = create_mock_companies()
            job_ids = create_mock_jobs(company_ids)
            application_ids = create_mock_applications(user_ids, job_ids, company_ids)
            
            print("\n" + "=" * 50)
            print("📊 Seeding Summary:")
            print(f"   👥 Users created: {len(user_ids)}")
            print(f"   🏢 Companies created: {len(company_ids)}")
            print(f"   💼 Jobs created: {len(job_ids)}")
            print(f"   📝 Applications created: {len(application_ids)}")
            print("\n✅ Database seeding completed successfully!")
            print("\n🎯 You can now test your API with realistic data!")
            print("📚 Access Swagger: http://localhost:5000/apidocs/")
            print("🗄️  Access Mongo Express: http://localhost:8081")
            
        except Exception as e:
            print(f"\n❌ Error during seeding: {str(e)}")
            sys.exit(1)

if __name__ == "__main__":
    main()