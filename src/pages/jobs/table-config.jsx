// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: MIT-0
import React from 'react';
import {
  CollectionPreferences,
  StatusIndicator,
  Link,
  Select,
  Input,
  Autosuggest,
  ButtonDropdown,
} from '@cloudscape-design/components';
import { createTableSortLabelFn } from '../../i18n-strings';
import {formatDateTime} from '../../common/utils';

const rawColumns = [
  {
    id: 'id',
    sortingField: 'id',
    header: 'ID',
    cell: item => (
      <div>
        <Link href={`/jobs/${item.job_id}`}>{item.job_id}</Link>
      </div>
    ),
    minWidth: 180,
  },
  {
    id: 'state',
    sortingField: 'state',
    header: 'State',
    cell: item => (
      <StatusIndicator type={item.job_status === 'SUCCESS' ? 'success' : 
        item.job_status === 'ERROR' ? "error" : 
        item.job_status === 'STOPPED' ? "stopped" : "in-progress"
      }>{item.job_status}</StatusIndicator>
    ),
    minWidth: 120,
  },
  {
    id: 'type',
    sortingField: 'type',
    cell: item => item.job_type,
    header: 'Type',
    minWidth: 160,
    isRowHeader: true,
  },
  {
    id: 'name',
    sortingField: 'name',
    cell: item => item.job_name,
    header: 'Name',
    minWidth: 160,
    isRowHeader: true,
  },
  {
    id: 'create_time',
    sortingField: 'create_time',
    cell: item => formatDateTime(item.job_create_time),
    header: 'Create Time',
    minWidth: 160,
    isRowHeader: true,
  },
  {
    id: 'start_time',
    sortingField: 'start_time',
    cell: item => formatDateTime(item.job_start_time),
    header: 'Start Time',
    minWidth: 160,
    isRowHeader: true,
  },
  {
    id: 'end_time',
    sortingField: 'end_time',
    cell: item => formatDateTime(item.job_end_time),
    header: 'End Time',
    minWidth: 160,
    isRowHeader: true,
  },
  {
    id: 'actions',
    header: 'Actions',
    minWidth: 100,
    cell: item => (
      <ButtonDropdown
        variant="inline-icon"
        ariaLabel={`${item.id} actions`}
        expandToViewport={true}
        items={[
          { id: 'view', text: 'View details' },
          { id: 'edit', text: 'Edit' },
          { id: 'delete', text: 'Delete' },
        ]}
      />
    ),
  },
];

export const COLUMN_DEFINITIONS = rawColumns.map(column => ({ ...column, ariaLabel: createTableSortLabelFn(column) }));

export const serverSideErrorsStore = new Map();

// Please do not use this in any real code, this is not a good regular expression for domain names
// A better regex would be something like: /^((?=[a-z0-9-]{1,63}\.)(xn--)?[a-z0-9]+(-[a-z0-9]+)*\.)+[a-z]{2,63}$/
// or one of the regular expressions mentioned here:
//    https://www.oreilly.com/library/view/regular-expressions-cookbook/9781449327453/ch08s15.html
export const domainNameRegex = /^(?:[\w_-]+\.){1,3}(?:com|net|org)$/i;
export const INVALID_DOMAIN_MESSAGE = 'Valid domain name ends with .com, .org, or .net.';

const editableColumns = {
  state: {
    minWidth: 200,
    editConfig: {
      ariaLabel: 'Edit state',
      errorIconAriaLabel: 'State Validation Error',
      editIconAriaLabel: 'editable',
      editingCell: (item, { setValue, currentValue }) => {
        const options = [
          { value: 'Activated', label: 'Activated' },
          { value: 'Deactivated', label: 'Deactivated' },
        ];
        return (
          <Select
            autoFocus={true}
            expandToViewport={true}
            ariaLabel="Select desired state"
            options={options}
            onChange={event => {
              setValue(event.detail.selectedOption.value);
            }}
            selectedOption={options.find(option => option.value === (currentValue ?? item.state))}
          />
        );
      },
    },
    cell: item => {
      return <StatusIndicator type={item.state === 'Deactivated' ? 'error' : 'success'}>{item.state}</StatusIndicator>;
    },
  },
  domainName: {
    minWidth: 180,
    editConfig: {
      ariaLabel: 'Edit domain name',
      errorIconAriaLabel: 'Domain Name Validation Error',
      editIconAriaLabel: 'editable',
      validation(item, value) {
        if (serverSideErrorsStore.has(item)) {
          if (value) {
            serverSideErrorsStore.set(item, domainNameRegex.test(value) ? undefined : INVALID_DOMAIN_MESSAGE);
          }
          return serverSideErrorsStore.get(item);
        }
      },
      editingCell: (item, { setValue, currentValue }) => {
        return (
          <Input
            autoFocus={true}
            ariaLabel="Edit domain name"
            value={currentValue ?? item.domainName}
            onChange={event => {
              setValue(event.detail.value);
            }}
            placeholder="Enter domain name"
          />
        );
      },
      disabledReason: item => {
        if (item.deliveryMethod === 'RTMP') {
          return 'You cannot change the domain name of an RTMP distribution.';
        }
        return undefined;
      },
    },
    cell: item => {
      return item.domainName;
    },
  },
  sslCertificate: {
    minWidth: 180,
    editConfig: {
      ariaLabel: 'Edit SSL certificate',
      errorIconAriaLabel: 'Certificate Validation Error',
      editIconAriaLabel: 'editable',
      editingCell: (item, { setValue, currentValue }) => {
        const options = [
          { value: 'Default', label: 'Default ' },
          { value: 'ACM', label: 'ACM' },
          { value: 'Custom', label: 'Custom' },
        ];
        return (
          <Autosuggest
            autoFocus={true}
            value={currentValue ?? item.sslCertificate}
            onChange={event => setValue(event.detail.value)}
            options={options}
            enteredTextLabel={value => `Use custom certificate "${value}"`}
            expandToViewport={true}
            ariaLabel="SSL Certificate"
            clearAriaLabel="clear"
            placeholder="Select an SSL certificate"
          />
        );
      },
    },
    cell: item => {
      return item.sslCertificate;
    },
  },
};

export const EDITABLE_COLUMN_DEFINITIONS = COLUMN_DEFINITIONS.map(column => {
  if (editableColumns[column.id]) {
    return {
      ...column,
      minWidth: Math.max(column.minWidth || 0, 176),
      ...editableColumns[column.id],
    };
  }
  return column;
});

const CONTENT_DISPLAY_OPTIONS = [
  { id: 'id', label: 'ID', alwaysVisible: true },
  { id: 'state', label: 'State' },
  { id: 'type', label: 'Type' },
  { id: 'name', label: 'Name' },
  { id: 'create_time', label: 'Create Time' },
  { id: 'start_time', label: 'Start Time' },
  { id: 'end_time', label: 'End Time' },
  { id: 'actions', label: 'Actions' },
];

export const PAGE_SIZE_OPTIONS = [
  { value: 10, label: '10 Records' },
  { value: 30, label: '30 Records' },
  { value: 50, label: '50 Records' },
];

export const DEFAULT_PREFERENCES = {
  pageSize: 30,
  contentDisplay: [
    { id: 'id', visible: true },
    { id: 'state', visible: true },
    { id: 'name', visible: true },
    { id: 'type', visible: true },
    { id: 'create_time', visible: true },
    { id: 'start_time', visible: false },
    { id: 'end_time', visible: false },
    { id: 'actions', visible: true },
  ],
  wrapLines: false,
  stripedRows: false,
  contentDensity: 'comfortable',
  stickyColumns: { first: 0, last: 1 },
};

export const Preferences = ({
  preferences,
  setPreferences,
  disabled,
  pageSizeOptions = PAGE_SIZE_OPTIONS,
  contentDisplayOptions = CONTENT_DISPLAY_OPTIONS,
}) => (
  <CollectionPreferences
    disabled={disabled}
    preferences={preferences}
    onConfirm={({ detail }) => setPreferences(detail)}
    pageSizePreference={{ options: pageSizeOptions }}
    wrapLinesPreference={{}}
    stripedRowsPreference={{}}
    contentDensityPreference={{}}
    contentDisplayPreference={{ options: contentDisplayOptions }}
    stickyColumnsPreference={{
      firstColumns: {
        title: 'Stick first column(s)',
        description: 'Keep the first column(s) visible while horizontally scrolling the table content.',
        options: [
          { label: 'None', value: 0 },
          { label: 'First column', value: 1 },
          { label: 'First two columns', value: 2 },
        ],
      },
      lastColumns: {
        title: 'Stick last column',
        description: 'Keep the last column visible while horizontally scrolling the table content.',
        options: [
          { label: 'None', value: 0 },
          { label: 'Last column', value: 1 },
        ],
      },
    }}
  />
);
