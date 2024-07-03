// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: MIT-0
import React, { useState, useEffect, useRef } from 'react';
import { Button, Form, Header, SpaceBetween, Link } from '@cloudscape-design/components';
import validateField from '../form-validation-config';
import DistributionsPanel from './jobinfo-panel';
import { remotePost } from '../../../../common/api-gateway';
import { useNavigate } from "react-router-dom";

// export const FormContext = React.createContext({});
// export const useFormContext = () => React.useContext(FormContext);

export function FormHeader({ loadHelpPanelContent }) {
  return (
    <Header
      variant="h1"
      description="Create a training job"
    >
      Create Training Job
    </Header>
  );
}

function FormActions({ onCancelClick ,readOnly}) {
  return (
    <SpaceBetween direction="horizontal" size="xs">
      <Button variant="link" onClick={onCancelClick}>
        Cancel
      </Button>
      {!readOnly&&<Button data-testid="create" variant="primary">
        Create
      </Button>}
    </SpaceBetween>
  );
}

function BaseForm({ content, readOnly,onCancelClick, errorText = null, onSubmitClick, header }) {
  return (
    <form
      onSubmit={event => {
        event.preventDefault();
        if (onSubmitClick) {
          onSubmitClick();
        }
      }}
    >
      <Form
        header={header}
        actions={<FormActions onCancelClick={onCancelClick} readOnly={readOnly}/>}
        errorText={errorText}
        errorIconAriaLabel="Error"
      >
        {content}
      </Form>
    </form>
  );
}

const defaultErrors = {
  model_name: null,
  prompt_template: null,
  job_type: null,
  job_name: null,
  dataset: null,
  training_stage: null,
  s3BucketSelectedOption: null,
  instance_num: null,
  instance_type: null
};

const fieldsToValidate = [
  'job_name',
  'job_type',
  'model_name',
  'dataset',
  'prompt_template',
  'training_stage',
  'instance_num',
  'instance_type'
  // 's3BucketSelectedOption',
];

export const FormWithValidation = ({ 
  loadHelpPanelContent, 
  header,
  setNotificationData,
  data,
  _setData,
  setDisplayNotify,
  readOnly
}) => {
  const [formErrorText, setFormErrorText] = useState(null);
  const [errors, _setErrors] = useState(defaultErrors);

  const setErrors = (updateObj = {}) => _setErrors(prevErrors => ({ ...prevErrors, ...updateObj }));
  const setData = (updateObj = {}) => _setData(prevData => ({ ...prevData, ...updateObj }));
  const navigate = useNavigate();

  const refs = {
    job_name: useRef(null),
    job_type: useRef(null),
    dataset: useRef(null),
    model_name: useRef(null),
    quant_type: useRef(null),
    training_stage: useRef(null),
    s3BucketSelectedOption: useRef(null),
    instance_type:useRef(null),
    instance_num:useRef(null),
    prompt_template:useRef(null),
    finetuning_method:useRef(null),
    learning_rate:useRef(null),
    batch_size:useRef(null),
    grad_accu:useRef(null),
    epoch:useRef(null),
    training_precision:useRef(null),
    max_samples:useRef(null),
    cutoff_length:useRef(null),
    val_size:useRef(null)
  };
  const onCancelClick =()=>
  {
    navigate('/jobs')
  }
  const onSubmit = () => {
    console.log(data);
    const newErrors = { ...errors };
    let validatePass = true;
    fieldsToValidate.forEach(attribute => {
      const { errorText } = validateField(attribute, data[attribute], data[attribute]);
      newErrors[attribute] = errorText;
      if (errorText) {
        console.log(errorText);
        validatePass = false;
      }
    });
    setErrors(newErrors);
    focusTopMostError(newErrors);
    console.log(validatePass);
    if (validatePass) {
      //submit 
      const formData = {
        job_name: data.job_name,
        job_type: data.training_stage,
        job_payload:{
          model_name: data.model_name,
          dataset: data.dataset,
          prompt_template: data.prompt_template,
          training_stage: data.training_stage,
          quant_type: data.quant_type,
          finetuning_method:data.finetuning_method,
          learning_rate:data.learning_rate,
          batch_size:data.batch_size,
          grad_accu:data.grad_accu,
          epoch:data.epoch,
          training_precision:data.training_precision,
          max_samples:data.max_samples,
          cutoff_length:data.cutoff_length,
          val_size:data.val_size,
          logging_steps:data.logging_steps,
          warmup_steps:data.warmup_steps,
          save_steps:data.save_steps,
          optimizer:data.optimizer,
          lora_rank:data.lora_rank,
          lora_alpha:data.lora_alpha,
          instance_type:data.instance_type,
          instance_num:data.instance_num
        },
    
      };
      remotePost(formData, 'v1/create_job').
        then(res => {
          setDisplayNotify(true);
          setNotificationData({ status: 'success', content: `Create job:${res.response_id}` });
          navigate('/jobs')
        })
        .catch(err => {
          setDisplayNotify(true);
          setNotificationData({ status: 'error', content: `Create job failed` });
        })
    }
  };

  const shouldFocus = (errorsState, attribute) => {
    let shouldFocus = errorsState[attribute]?.length > 0;

    if (attribute === 'functions' && !shouldFocus) {
      shouldFocus = errorsState.functionFiles?.length > 0;
    }

    return shouldFocus;
  };

  const focusTopMostError = errorsState => {
    for (const [attribute, ref] of Object.entries(refs)) {
      if (shouldFocus(errorsState, attribute)) {
        if (ref.current?.focus) {
          return ref.current.focus();
        }

        if (ref.current?.focusAddButton) {
          return ref.current.focusAddButton();
        }
      }
    }
  };

  return (
    <BaseForm
      header={header}
      content={
        <SpaceBetween size="l">
          <DistributionsPanel
            loadHelpPanelContent={loadHelpPanelContent}
            validation={true}
            data={data}
            errors={errors}
            setData={setData}
            setErrors={setErrors}
            refs={refs}
            readOnly={readOnly}
          />
        </SpaceBetween>
      }
      onSubmitClick={onSubmit}
      readOnly={readOnly}
      onCancelClick={onCancelClick}
      errorText={formErrorText}
    />
  );
};
