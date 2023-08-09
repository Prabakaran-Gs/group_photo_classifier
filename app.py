from flask import Flask,render_template,send_file,url_for,request,session
import os
import shutil
import face_recognition
import cv2 as cv
import threading

app = Flask(__name__)
unique_faces = []
unique_details = []
unique_count = 0
duplicate_count=0
image_count = 0

def run_ml_model(filename):
    startproject(filename)

    unique_face_identifier(filename)
    create_file(unique_count,filename)
    photo_sep(filename,unique_details)

def startproject(filename):
    global unique_faces  ; unique_faces = []
    global  unique_details ; unique_details = []
    global  unique_count; unique_count = 0
    global duplicate_count; duplicate_count=0
    global image_count ; image_count = 0
    os.makedirs(os.path.join(filename,"album"))   # os.makedirs("album")(os.jo)
    os.makedirs(os.path.join(filename,"dup_photo")) # os.makedirs("dup_photo")
    os.makedirs(os.path.join(filename,"unique_photo")) # os.makedirs("unique_photo")
    os.makedirs(os.path.join(filename,"users")) # os.makedirs("users")

def create_file(n,filename):
    for i in range(1,n+1):
        os.makedirs(os.path.join(filename,"album/"+str(i)))

def unique_face_identifier(filename):
    global unique_count
    global duplicate_count
    global unique_faces
    global unique_details
    global image_count

    for files in os.listdir(filename+"/group_photo"):
        image = cv.imread(filename+"/group_photo/"+files)
        image_count +=1
        image_rgb = cv.cvtColor(image,cv.COLOR_BGR2RGB)
        #stores all faces
        faces = face_recognition.face_locations(image_rgb)
        print(f"NO of faces in pic {image_count} = {len(faces)}")

        for face in faces:
            a,b,c,d = face
            details = face_recognition.face_encodings(image_rgb,[face])[0]
            unique = True
            if len(unique_faces) == 0:
                unique_faces.append(face) 
                unique_details.append(details)
                unique_count+=1;cv.imwrite(os.path.join(filename,"unique_photo/"+str(unique_count)+".jpeg"),image[a:c,d:b])
            else:
                for u_detail in unique_details:
                    if face_recognition.compare_faces([u_detail],details,tolerance=0.40)[0] :
                        duplicate_count+=1;cv.imwrite(os.path.join(filename,"dup_photo/"+str(duplicate_count)+".jpeg"),image[a:c,d:b])
                        unique =False 
                        break;
                if unique:
                    unique_faces.append(face)
                    unique_details.append(details)
                    unique_count+=1;cv.imwrite(os.path.join(filename,"unique_photo/"+str(unique_count)+".jpeg"),image[a:c,d:b])


def photo_sep(filename,unique_detail):
    for image_file in os.listdir(filename+"/group_photo"):
        image = cv.imread(filename+"/group_photo/"+image_file)
        image_rgb = cv.cvtColor(image,cv.COLOR_BGR2RGB)
        face_details = face_recognition.face_encodings(image_rgb)
        for subfile,knownfaces in enumerate(unique_detail):
            for unknownfaces in face_details:
                if face_recognition.compare_faces([knownfaces],unknownfaces,tolerance=0.40)[0]:
                    loacation = "album/"+str(subfile+1)+"/"+image_file+".jpeg"
                    loacation = os.path.join(filename,loacation)
                    cv.imwrite(loacation,image)
    print("Photo Seperated Successfully")

def check_for_face(image_pth):
    image_bgr = cv.imread(image_pth)
    image = cv.cvtColor(image_bgr,cv.COLOR_BGR2RGB)
    print("image Readed Success")
    detail = face_recognition.face_encodings(image)[0]
    for filename,faces in enumerate(unique_details):
        print("*****")
        if face_recognition.compare_faces([detail], faces,tolerance = 0.45 )[0]:
            print(f"Your file naame is {filename+1}")
            return str(filename+1)





######################################################################################################

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/newevent',methods=['POST'])
def newevent():
    session["event_name"] = request.form['event_name']
    session["email"] = request.form['email']
    return render_template('newevent.html',event_name = session.get("event_name"),email = session.get("email"))


@app.route("/oldevent",methods=['POST'])
def oldevent():
    session["event_name"] = request.form['event_name']
    return render_template('oldevent.html',filename = session.get("event_name"))

@app.route("/result",methods=['POST'])
def result():
    user_name = request.form['name']
    image = request.files['photo']
    print(image.filename)
    event_name = session.get("event_name")
    image.save(f'{event_name}/users/{image.filename}')
    location = event_name+"/users/"+image.filename 
    file_name = str(check_for_face(location))
    print(file_name)
    zip_location = os.path.join(event_name,"zip_files",user_name)
    file_loader = os.path.join(event_name,"album",file_name)
    print(file_loader)
    shutil.make_archive(zip_location, 'zip', file_loader)
    return send_file(zip_location+".zip")
    # return "HI"
    


@app.route('/process/<event_name>',methods=['POST'])
def process(event_name):
    images = request.files.getlist("images")
    os.makedirs(event_name+"/group_photo")
    for file in images:
        if file.filename != '':
            file.save(f'{event_name}/group_photo/{file.filename}')
    arg1 = event_name
    ml_thread = threading.Thread(target=run_ml_model, args=(arg1,))
    ml_thread.start()
    
    return "Processing output will be sent to " + session["email"]

if __name__ == '__main__':
    app.run(debug=True)