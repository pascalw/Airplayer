import os

def clear_folder(folder):
    """
    Remove the given folder's content.
    """
    for the_file in os.listdir(folder):
        file_path = os.path.join(folder, the_file)
        try:
            if os.path.isfile(file_path):
                os.unlink(file_path)
        except Exception, e:
            print e
            
def clean_hostname(hostname):
    """
    Remove the .local appendix of a hostname.
    """
    if hostname:
        return hostname.replace('.local', '')