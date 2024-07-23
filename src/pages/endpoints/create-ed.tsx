// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: MIT-0
import React ,{useEffect, useState} from 'react';
import { Button, Modal, Box, RadioGroup,RadioGroupProps,FormField, Toggle,SpaceBetween,Select,SelectProps } from '@cloudscape-design/components';
import { remotePost } from '../../common/api-gateway';

interface PageHeaderProps {
  extraActions?: React.ReactNode;
  selectedItems:ReadonlyArray<any>,
  visible: boolean;
  setVisible: (value: boolean) => void;
  setDisplayNotify: (value: boolean) => void;
  setNotificationData: (value: any) => void;
  onDelete?: () => void;
  onRefresh?: () => void;
}

interface SelectInstanceTypeProps {
    data:any;
    setData: (value: any) => void;
    readOnly: boolean;
    // refs?:Record<string,React.RefObject<any>>;
}

const defaultErrors={
    instance_type:null,
    engine:null,
    enable_lora:null
}


const  INSTANCE_TYPES : SelectProps.Option[] =[
    { label: 'ml.g4dn.2xlarge', value: 'ml.g4dn.2xlarge' },
    { label: 'ml.g4dn.12xlarge', value: 'ml.g4dn.12xlarge' },
    { label: 'ml.g5.2xlarge', value: 'ml.g5.2xlarge' },
    { label: 'ml.g5.12xlarge', value: 'ml.g5.12xlarge' },
    { label: 'ml.g5.48xlarge', value: 'ml.g5.48xlarge' },
    { label: 'ml.p4d.24xlarge', value: 'ml.p4d.24xlarge' },
    { label: 'ml.p4de.24xlarge', value: 'ml.p4de.24xlarge' },
    { label: 'ml.p5.48xlarge', value: 'ml.p5.48xlarge' }
  ]

const ENGINE : RadioGroupProps.RadioButtonDefinition[]= [
    { label:'vllm',value:'vllm'},
    { label:'lmi-dist',value:'lmi-dist'},
    { label:'trt-llm',value:'trt-llm'},
    { label:'HF accelerate',value:'scheduler'}
]

const defaultData = {
    instance_type:'ml.g5.2xlarge',
    engine:'vllm',
    enable_lora:false,
  }
const SelectInstanceType = ({ data, setData, readOnly }:SelectInstanceTypeProps)  => {
    const [selectOption, setSelectOption] = useState<SelectProps.Option| null>(INSTANCE_TYPES[2]);
    return (
      <Select
        selectedOption={selectOption}
        disabled={readOnly}
        onChange={({ detail }) => {
          setSelectOption(detail.selectedOption);
          setData((pre:any) => ({...pre, instance_type: detail.selectedOption.value }))
        }}
        options={INSTANCE_TYPES}
        selectedAriaLabel="Selected"
      />
    )
  }

  const SetEngineType = ({ data, setData, readOnly }:SelectInstanceTypeProps)  => {
    const [value,setValue] = useState <string|null> (ENGINE[0].value);
    return (
      <RadioGroup
        items={ENGINE}
        readOnly={readOnly}
        value={value}
        onChange={({ detail }) => {
            setValue(detail.value);
          setData((pre:any) => ({...pre, engine: detail.value }))

        }}
      />
    )
  }

  const EnableLora = ({ data, setData, readOnly }:SelectInstanceTypeProps)  => {
    const [checked,setChecked] = useState <boolean> (false);
    return(
        <Toggle
        onChange={({ detail }) =>{
          setChecked(detail.checked);
          setData((pre:any) => ({...pre, enable_lora: detail.checked }))
        }
        }
        checked={checked}
      >
        Enable
      </Toggle>
      )
    
  }

export const DeployModelModal = ({
    extraActions = null,
    selectedItems,
    visible,
    setVisible,
    setDisplayNotify,
    setNotificationData,
    ...props
  }: PageHeaderProps) => {
    const [errors, _setErrors] = useState(defaultErrors);
    const [data, setData] = useState(defaultData);
    console.log(data)
    const onDeloyConfirm =()=>{
        const jobId = selectedItems[0].job_id
        const fromData = {...data,job_id:jobId}
        remotePost(fromData, 'deploy_endpoint').
        then(res => {
            if (res.response.result) {
              setVisible(false);
              setDisplayNotify(true);
              setNotificationData({ status: 'success', content: `Create Endpoint Name:${res.response.endpoint_name}` });
            }
        
        })
        .catch(err => {
          setDisplayNotify(true);
          setVisible(false);
          setNotificationData({ status: 'error', content: `Create Endpoint failed` });
        })
    }
    return (
      <Modal
        onDismiss={() => setVisible(false)}
        visible={visible}
        footer={
          <Box float="right">
            <SpaceBetween direction="horizontal" size="xs">
              <Button variant="link" onClick={()=> setVisible(false)}>Cancel</Button>
              <Button variant="primary" onClick={onDeloyConfirm}>Confirm</Button>
            </SpaceBetween>
          </Box>
        }
        header="Deploy model as endpoint"
      ><SpaceBetween size="l">
          <FormField
            label="Instance Type"
            description="Select a Instance type to deploy the model."
            stretch={false}
            errorText={errors.instance_type}
            i18nStrings={{ errorIconAriaLabel: 'Error' }}
          >
            <SelectInstanceType data={data} setData={setData} readOnly={false} />
          </FormField>

          <FormField
            label="Engine Type"
            stretch={false}
            errorText={errors.engine}
            i18nStrings={{ errorIconAriaLabel: 'Error' }}
          >
            <SetEngineType data={data} setData={setData} readOnly={false}/>
          </FormField>

          {/* <FormField
            label="Enable Lora Adapter"
            stretch={false}
            errorText={errors.enable_lora}
            i18nStrings={{ errorIconAriaLabel: 'Error' }}
          >
            <EnableLora data={data} setData={setData} readOnly={false}/>
          </FormField> */}
        </SpaceBetween>
      </Modal>
    );
  }