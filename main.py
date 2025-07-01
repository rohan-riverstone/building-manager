from mcp.server.fastmcp import FastMCP
import psycopg2
from psycopg2.extras import RealDictCursor
import os
from datetime import datetime
from typing import List
import json
import sys
import psycopg2
import os
from dotenv import load_dotenv
from datetime import datetime
import re

load_dotenv(override=True)
# from system.config import Config 

# Load config from local_settings.json
# config_loader = Config()
# config = config_loader.get_config()

    
class DatabaseManager:
    def __init__(self):
        self.connection = None
        self.connect()
#       self.setup_database()
    
    def connect(self):
        try:
            self.pgconnection = psycopg2.connect(
                host=os.getenv('POSTGRES_HOST'),
                port=os.getenv('POSTGRES_PORT', '5432'),
                database=os.getenv('POSTGRES_DATABASE'),
                user=os.getenv('POSTGRES_USER'),
                password=os.getenv('POSTGRES_PASSWORD')
            )
            self.pgcursor = self.pgconnection.cursor()

            tenant_name = "tenant"+str(os.getenv('TENANT_ID'))+""
            set_path_query = f"set search_path = "+str(tenant_name)+""
            self.pgcursor.execute(set_path_query)
            print("connection successful")

        except psycopg2.Error as e:
            print(f"Error connecting to database: {e}")
            raise

    def execute_query(self, query, data=None):
        try:
            self.pgcursor.execute(query, data)
            self.pgconnection.commit()
        except psycopg2.Error as e:
            print(f"Error executing query: {e}")
            self.pgconnection.rollback()
            raise

    def get_assets_from_building(self, building_id: int) -> List[dict]:
        if not building_id:
            return "please provide the building id"
        """Get assets from the table"""
        query = """
        select name from tenant5.assets where building_id = %s
        """
        
        try:
            with self.connection.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(query, (building_id,))
                results = cursor.fetchall()
                return [dict(row) for row in results]
        except Exception as e:
            print(f"Error getting leave history: {e}")
            return []
        
    # def create_building(self, name: str):
    #     if not name:
    #         return "please provide a name for the building"
    #     """Add a building with its name and return the new building's ID."""
    #     building_insert_query = "INSERT INTO tenant5.buildings (name) VALUES (%s) RETURNING id"
    #     try:
    #         with self.connection.cursor(cursor_factory=RealDictCursor) as cursor:
    #             cursor.execute(building_insert_query, (name))
    #             result = cursor.fetchone()[0]
    #             self.connection.commit()
    #             return result
    #     except Exception as e:
    #         print(f"Error creating building: {e}")
    #         self.connection.rollback()
    #         return None
    
    def get_or_create_building_id_by_name(self,name: str=None):
        if not name:
            return "provide a name"
        select_query="select id from tenant5.buildings where name=%s"
        select_data=(name,)
        self.execute_query(select_query,select_data)
        print(f"inserted into buildings with name:{name}")
        building_id=self.pgcursor.fetchone()
        if building_id:
            return building_id[0]
        
        insert_query="INSERT INTO tenant5.buildings (name) VALUES (%s) RETURNING id"
        insert_data=(name,)
        self.execute_query(insert_query,insert_data)
        print(f"inserted into buildings with name:{name}")
        building_id=self.pgcursor.fetchone()[0]
        if building_id:
            return building_id

    
    def create_alarm_devices(self,location: str=None,alarm_system_id: int=None,alarm_device_type_id: int=None):
        
        if not location:
            return "Please provide the location"

        if not alarm_system_id:
            return "Please provide the alarm system id"
        
        if not alarm_device_type_id:
            return "Please provide the alarm device type id"
        
        query = "INSERT INTO tenant5.alarm_devices (location,alarm_system_id,alarm_device_type_id) VALUES (%s, %s, %s)  returning id"

        data = (location,alarm_system_id,alarm_device_type_id)
        
        self.execute_query(query, data)
        alarm_device_id=self.pgcursor.fetchone()[0]
        return alarm_device_id

    def create_alarm_system(self,name: str = None, building_name: str = None):
        if not name:
            return "please provide the name"
        if not building_name:
            return "Enter the building name"
        
        building_id=self.get_or_create_building_id_by_name(building_name)
        if building_id:
            query= "insert into tenant5.alarm_systems (name,building_id) values(%s,%s) returning id"
            data=(name,building_id)
            self.execute_query(query,data)
            alarm_system_id=self.pgcursor.fetchone()[0]
            if alarm_system_id:
                return f"alarm system created id: {alarm_system_id}"
        return "not created"
    
    def get_alarm_device_types_id(self,name: str=None):
        if not name:
            return "Please provide a name for the alarm device type"
        
        get_query="select id from alarm_device_types where type_name=%s"
        data=(name,)
        self.execute_query(get_query,data)
        alarm_device_type_id=self.pgcursor.fetchone()
        if alarm_device_type_id:
            return alarm_device_type_id[0]
        
        insert_query="Insert into alarm_device_types (type_name) values (%s) returning id"
        insert_data=(name,)
        self.execute_query(insert_query,insert_data)
        alarm_device_type_id=self.pgcursor.fetchone()[0]
        if alarm_device_type_id:
            return alarm_device_type_id
        return "not created"
    
db_manager=DatabaseManager()

mcp = FastMCP("BuildingManagement")

@mcp.tool()
def get_assets_from_building(building_id: int) -> str:
    """get the assets used in the building"""
    building_data = db_manager.get_assets_from_building(building_id)
    
    if building_data:
        names = ', '.join(asset['name'] for asset in building_data)
        return f"Building {building_id} has assets: {names}"
    return "connection issue"

@mcp.tool()
def get_or_create_building_id_by_name(name: str):
    """Get or create a building by name, return its ID."""
    building_id = db_manager.get_or_create_building_id_by_name(name)
    if building_id:
        return f"Building ID for '{name}' is {building_id}"
    return "Could not create or fetch building ID."

@mcp.tool()
def create_alarm_devices(location: str, alarm_system_id: str, alarm_device_type_id: str):
    """Add the the alarm device in the table"""
    alarm_device_id=db_manager.create_alarm_devices(location=location,alarm_system_id=alarm_system_id, alarm_device_type_id=alarm_device_type_id)
    if alarm_device_id:
        return f"created alarm device with id: {alarm_system_id}"
    return "Could not create alarm device"

@mcp.tool()
def create_alarm_system(name: str, building_name: str):
    "adding all the alarm system"
    alarm_system_id=db_manager.create_alarm_system(name,building_name)
    if alarm_system_id:
        return f"Created alarm system with id: {alarm_system_id}"
    return "could not create alarm system"

@mcp.tool()
def get_alarm_device_types_id(name:str):
    """get alarm device type id from the table"""
    alarm_device_type_id = db_manager.get_alarm_device_types_id(name)
    if alarm_device_type_id:
        return f"got the id from the alarm device type table: {alarm_device_type_id}"
    return "Could not create device"

# @mcp.fallback_tool()
# def fallback(input_text: str) -> str:
#     """Fallback handler when Claude doesn't find a matching tool."""
#     return (
#         "I'm here to help you manage buildings, alarm systems, and devices. "
#         "I can't help with pizza orders 😅. Try asking me something like: "
#         "'Add a smoke detector to the lobby in Building A'."
#     )

@mcp.tool()
def handle_unknown_request(input_text: str) -> str:
    """Handles unclear or unsupported user requests."""
    return (
        f"I'm not sure how to help with: '{input_text}'. "
        "Try something like 'Add a new building' or 'Register a smoke detector.'"
    )


def cleanup():
    db_manager.close()

if __name__ == "__main__":
    try:
        print("starting main")
        mcp.run()
    except Exception as ex:
        try:
            print(ex)
        except Exception:
            sys.stderr.write("Shutdown message suppressed (stdout closed)\n")
        db_manager.close()
