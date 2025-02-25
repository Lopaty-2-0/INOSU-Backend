def sendResponse(statuscode, resCode, data, resType):
    return  {
        "statuscode": statuscode,
        "resCode": resCode,
        "data": data,
        "resType": resType
    }, statuscode