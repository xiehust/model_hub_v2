// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: MIT-0
import React, { useRef, useState } from 'react';
// import { createRoot } from 'react-dom/client';
import { CustomAppLayout, Navigation, Notifications } from '../../commons/common-components';
import {Breadcrumbs,createjobBreadcrumbs} from '../../commons/breadcrumbs'

import { FormHeader,FormWithValidation} from './components/form';
// import ToolsContent from './components/tools-content';
import '../../../styles/form.scss';

const defaultData = {
  model_name: null,
  prompt_template: null,
  job_type: 'lora',
  job_name: '',
  quant_type: 'none',
  finetuning_method:'lora',
  training_stage: '',
  learning_rate:'5e-5',
  batch_size:2,
  grad_accu:8,
  epoch:3.0,
  training_precision:'fp16',
  max_samples:50000,
  cutoff_length:1024,
  val_size:0.0,
  logging_steps:10,
  warmup_steps:10,
  save_steps:500,
  optimizer:'adamw_torch',
  lora_rank:8,
  lora_alpha:16,
  instance_type:null,
  instance_num:1,
};


const CreateJobApp =() => {
  const [toolsIndex, setToolsIndex] = useState(0);
  const [toolsOpen, setToolsOpen] = useState(false);
  const appLayout = useRef();
  const [notificationData, setNotificationData] = useState({});
  const [displayNotify, setDisplayNotify] = useState(false);
  const [data, _setData] = useState(defaultData);

  const loadHelpPanelContent = index => {
    setToolsIndex(index);
    setToolsOpen(true);
    appLayout.current?.focusToolsClose();
  };

  return (
    <CustomAppLayout
      ref={appLayout}
      contentType="form"
      content={
        <FormWithValidation
          loadHelpPanelContent={loadHelpPanelContent}
          data={data}
          _setData={_setData}
          setNotificationData={setNotificationData}
          setDisplayNotify={setDisplayNotify}
          header={<FormHeader loadHelpPanelContent={loadHelpPanelContent} />}
        />
      }
      breadcrumbs={<Breadcrumbs items={createjobBreadcrumbs}/>}
      navigation={<Navigation activeHref="#/jobs" />}
      // tools={ToolsContent[toolsIndex]}
      toolsOpen={toolsOpen}
      onToolsChange={({ detail }) => setToolsOpen(detail.open)}
      notifications={<Notifications 
        successNotification={displayNotify}
      data={notificationData}/>}
    />
  );
}


export default CreateJobApp;
// createRoot(document.getElementById('app')).render(<App />);
