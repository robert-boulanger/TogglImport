#!/opt/homebrew/bin/python3


import argparse
from datetime import datetime
import json
startdir = "/Users/robert/Documents/Stundenlisten"

try:
    from toggl.TogglPy import Toggl, Endpoints
except:
    print("You first have to install Togglpy (pip install -U TogglPy from command line)")
    print("To avoid ssl certification errors also install certifi.(pip install -U certifi from command line)")

class DetailedToggle(Toggl):
    """Overwritten default method since togglpy only supports hours and no minutes for start times"""
    def __init__(self):
        Toggl.__init__(self)

    def createTimeEntry(self,start, secondduration:int, description:str=None, projectid:str=None, projectname:str=None,
                        taskid:str=None, clientname:str=None, ):
        """
        Creating a custom time entry, minimum must is hour duration and project param
        :param secondduration:
        :param description: Sets a descripton for the newly created time entry
        :param projectid: Not required if projectname given
        :param projectname: Not required if projectid was given
        :param taskid: Adds a task to the time entry (Requirement: Toggl Starter or higher)
        :param clientname: Can speed up project query process
        :param start: Taken from now() if not provided

        """
        data = {
            "time_entry": {}
        }

        if not projectid:
            if projectname and clientname:
                projectid = (self.getClientProject(clientname, projectname))['data']['id']
            elif projectname:
                projectid = (self.searchClientProject(projectname))['data']['id']
            else:
                print('Too many missing parameters for query')
                exit(1)
        if description:
            data['time_entry']['description'] = description
        if taskid:
            data['time_entry']['tid'] = taskid
        data['time_entry']['start'] = start
        data['time_entry']['duration'] = secondduration
        data['time_entry']['pid'] = projectid
        data['time_entry']['created_with'] = 'RB Toggl Importer'

        response = self.postRequest(Endpoints.TIME_ENTRIES, parameters=data)
        return self.decodeJSON(response)

def readFile():
    parser = argparse.ArgumentParser()
    parser.add_argument('filename', help="name of the file to process", type=str)
    parser.add_argument('key', help='Toggle Key', type=str, default='secret')
    args = parser.parse_args()
    API_TOKEN = args.key
    import_file = args.filename
    print(import_file, API_TOKEN)
    toggl = DetailedToggle()
    toggl.setAPIKey(API_TOKEN)
    response = toggl.request("https://api.track.toggl.com/api/v8/clients")
    taskcache = {}
    projectcache = {}
    project_object = None
    with open(import_file, "r") as i_file:
        fdata = json.load(i_file)
        for entry in fdata['data']:
            start = entry["start"]
            duration = int(entry['duration']) * 60
            task = entry["task"]
            project = entry["project"]
            client = entry["category"]
            description = entry["note"]
            if project in projectcache.keys():
                project_object = projectcache[project]
            else:
                project_object = toggl.getClientProject(client, project)
                projectcache[project] = project_object
            project_id = project_object['data']['id']
            if task in taskcache.keys():
                taskid = taskcache[task]
            else:
                for taskentry in toggl.getProjectTasks(project_id):
                    if taskentry['name'] == task:
                        taskid = taskentry['id']
                        taskcache[task] = taskid
                        break
            sd = datetime.fromisoformat(start)
            if sd.weekday() < 5: # No Weekends
                print("sending")
                print(f"duration, {duration} description={description}, projectid={project_id}, projectname={project},taskid={taskid}, clientname={client}, start={start}")
                print("received")
                resp = toggl.createTimeEntry(start, duration,description=description, projectid=project_id, projectname=project,taskid=taskid, clientname=client)
                print("==============================================")
            else:
                print('skipping Wed to Friday',start)


if __name__ == "__main__":

    readFile()