// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: MIT-0
import React, { useEffect, useState,useCallback,useRef } from 'react';
import { remotePost } from '../../../../common/api-gateway';
import Textarea from "@cloudscape-design/components/textarea";
import FormField from "@cloudscape-design/components/form-field";
import Button from "@cloudscape-design/components/button";
import Container  from '@cloudscape-design/components/container';
import Header from "@cloudscape-design/components/header";
import Badge from "@cloudscape-design/components/badge";
import {JOB_STATE} from "../../table-config";
const defaultRows = 20;
const defaultMaxRows = 50;
export const LogsPanel = ({jobRunName,jobStatus,jobId}) => {
    const [logs, setLogs] = useState(['Start running, please wait a few minutes...']);
    const [loading, setLoading] = useState(false);
    const [rows, setRows] = useState(defaultRows);
    const [stop,setStop] = useState(true);
    const [newJobStatus, setNewStatus] = useState(jobStatus);
    const intervalRef = useRef(null);
    const intervalRef2 = useRef(null);

    const fetchLogs = useCallback(() => {
        setLoading(true);
        const params = {"job_run_name": jobRunName};
        //获取日志
        remotePost(params, 'fetch_training_log').then((res) => {
            setLoading(false);
            if (res.log_events.length ){
                setLogs(res.log_events);
                setRows(res.log_events.length > defaultRows ?
                    (res.log_events.length > defaultMaxRows ? defaultMaxRows : res.log_events.length) : defaultRows);
            }

        }).catch(err => {
            setLoading(false);
            setLogs(prev => [...prev, JSON.stringify(err)])
        });
    }, [jobRunName]);

    useEffect(() => {
        fetchLogs();
        //只有在RUNNING
        if (newJobStatus === JOB_STATE.RUNNING){
            intervalRef.current  = setInterval(fetchLogs, 10000);  // 每10秒刷新一次
            setStop(false)
        }
            
        return () => {
            intervalRef && clearInterval(intervalRef.current );  // 清除定时器
        };
    }, []);
    const onRefresh = () => {
        fetchLogs();  // 手动刷新时调用fetchLogs
    };

    const fetchStatus = useCallback(() => {
        remotePost({"job_id":jobId}, 'get_job_status').then((res) => {
            console.log('status:',res.job_status);
            setNewStatus(res.job_status);
            if (res.job_status !== 'RUNNING'){
                intervalRef && clearInterval(intervalRef.current );  // 清除取log定时器
            }
        }).catch(err => {
            console.log(err);
        })
    }, [jobRunName]);

    useEffect(() => {
        fetchStatus()
        intervalRef2.current  = setInterval(fetchStatus, 10000);  // 每10秒刷新一次
        //在最终状态时停止
        if ((newJobStatus === JOB_STATE.SUCCESS ||  
             newJobStatus === JOB_STATE.ERROR ||
             newJobStatus === JOB_STATE.STOPPED ||
             newJobStatus === JOB_STATE.TERMINATED
        )){
            clearInterval(intervalRef2.current );  // 清除定时器
        }
        return () => {
            clearInterval(intervalRef2.current );  // 清除定时器
        };
    }, []);

    const stateToColor = (status) => {
        switch (status) {
            case JOB_STATE.RUNNING:
                return 'blue';
            case JOB_STATE.SUCCESS:
                return 'green';
            case JOB_STATE.ERROR:
                return 'red';
            case JOB_STATE.STOPPED:
                return 'red';
            case JOB_STATE.TERMINATED:
                return'red';
        }
    }


    return (
        <Container
            header={<Header variant="h2"
            info={<Badge color={stateToColor(newJobStatus)}>{newJobStatus}</Badge>}
            >Training Logs</Header>}
        >
        <FormField
          label={`SageMaker Training Job Name: ${jobRunName}`}
          secondaryControl={<Button data-testid="header-btn-refresh" 
            iconName="refresh" 
            loading={loading}
            disabled={stop}
            onClick={onRefresh} >Reloading</Button>}
          stretch={true}
        >
            <Textarea  value={logs.join('\n')} readOnly rows={rows}/>
        </FormField>
        </Container>

    )
}
