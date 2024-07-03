// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: MIT-0
import uniq from 'lodash/uniq';
import { SelectProps } from '@cloudscape-design/components';

type FormDataAttributes =
  | 'cloudFrontRootObject'
  | 'alternativeDomainNames'
  | 's3BucketSelectedOption'
  | 'certificateExpiryDate'
  | 'certificateExpiryTime'
  | 'httpVersion'
  | 'ipv6isOn'
  | 'functions'
  | 'originId'
  | 'customHeaders';

const validateEmpty = (value: string | undefined | null | File[]) => Boolean(value && value.length > 0);

const validateURLPrefix = (value: string) => value.startsWith('https://') || value.startsWith('http://');

const validateURLFormat = (value: string) => {
  const urlFormatRegex = new RegExp(/^([a-zA-Z0-9]{1,63}\.)+[a-zA-Z]{2,}$/);
  // strip valid url prefixes
  let url = value;
  url = url.replace('http://', '');
  url = url.replace('https://', '');

  return urlFormatRegex.test(url);
};

const validateCNAMEs = (value: string) => {
  if (!value) {
    return true;
  }

  const CNAMEs = value.split(',');
  return CNAMEs?.length < 4;
};
const validateFileSize = (file: File) => file.size <= 500;

const validateS3Bucket = (value: string) => {
  return !value.includes('NO-ACCESS');
};

const URLSpecialCharacterRegex = new RegExp(/[^A-Za-z0-9:/.]/gm);
const originIdSpecialCharacterRegex = new RegExp(/[^A-Za-z0-9-.]/gm);
const validateSpecialCharacter = (value: string, regex: RegExp) => {
  const isValid = !regex.test(value);

  return isValid;
};
const getSpecialCharacters = (value: string, regex: RegExp) => {
  const specialCharacters = value.match(regex);
  return uniq(specialCharacters);
};


const validateNumers = (value: string) => {
  const numberRegex = new RegExp(/[^0-9]/gm);
  const isValid = !numberRegex.test(value);
  return isValid;
};

const validateEmptyCharacter = (value: string) => !value?.includes(' ');
const validateCodeEditor = (value: string | undefined | null) => Boolean(!value || value.length === 0);

type ValidationFunction = (value: any) => boolean;
type ValidationText = string | ((value: string) => string);

const validationConfig: Record<
  string,
  Array<{ validate: ValidationFunction; errorText?: ValidationText; warningText?: ValidationText }>
> = {
  job_name: [{ validate: validateEmpty, errorText: 'Job name is required.' }],
  model_name: [{ validate: validateEmpty, errorText: 'Model name is required.' }],
  prompt_template: [{ validate: validateEmpty, errorText: 'Prompt template name is required.' }],
  job_type: [{ validate: validateEmpty, errorText: 'Finetune type is required.' }],
  dataset:[{ validate: validateEmpty, errorText: 'Dataset is required.' }],
  training_stage: [{ validate: validateEmpty, errorText: 'Training Stage type is required.' }],
  instance_type: [{ validate: validateEmpty, errorText: 'Instance type is required.' }],
  instance_num: [//{ validate: validateEmpty, errorText: 'Instance amount is required.' },
    {validate:validateNumers,errorText: 'Only integer is supported.' }
  ],
  s3BucketSelectedOption: [
    {
      validate: (selectedOption: SelectProps.Option) => validateEmpty(selectedOption?.value),
      errorText: 'S3 bucket is required.',
    },
    {
      validate: (selectedOption: SelectProps.Option) => validateS3Bucket(selectedOption?.label || ''),
      errorText:
        "Model Hub isn't allowed to access to this bucket. You must enable access control lists (ACL) for the bucket.",
    },
  ],
};

export default function validateField(attribute: FormDataAttributes, value: any, customValue: string = value) {
  const validations = validationConfig[attribute];
  // console.log('validations', attribute,validations);
  if(validations){
    for (const validation of validations) {
      const { validate, errorText, warningText } = validation;
  
      const isValid = validate(value);
      if (!isValid) {
        return {
          errorText: typeof errorText === 'function' ? errorText(customValue) : errorText,
          warningText: typeof warningText === 'function' ? warningText(customValue) : warningText,
        };
      }
    }
  }
  return { errorText: null };
}
