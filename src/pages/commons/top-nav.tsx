// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: MIT-0
import React, { useState } from 'react';
import TopNavigation from '@cloudscape-design/components/top-navigation';
import { isVisualRefresh } from '../../common/apply-mode';

import '../../styles/base.scss';
import '../../styles/top-navigation.scss';

import logo from '../../resources/smlogo.svg';



const i18nStrings = {
    searchIconAriaLabel: 'Search',
    searchDismissIconAriaLabel: 'Close search',
    overflowMenuTriggerText: 'More',
    overflowMenuTitleText: 'All',
    overflowMenuBackIconAriaLabel: 'Back',
    overflowMenuDismissIconAriaLabel: 'Close menu',
  };
  
  const profileActions = [
    { id: 'profile', text: 'Profile' },
    { id: 'preferences', text: 'Preferences' },
    { id: 'security', text: 'Security' },
    {
      id: 'support-group',
      text: 'Support',
      items: [
        {
          id: 'documentation',
          text: 'Documentation',
          href: '#',
          external: true,
          externalIconAriaLabel: ' (opens in new tab)',
        },
        { id: 'feedback', text: 'Feedback', href: '#', external: true, externalIconAriaLabel: ' (opens in new tab)' },
        { id: 'support', text: 'Customer support' },
      ],
    },
    { id: 'signout', text: 'Sign out' },
  ];


export const TopNav = () =>{

    return (
<TopNavigation
i18nStrings={i18nStrings}
identity={{
  href: '#',
  title: 'Service name',
  logo: { src: logo, alt: 'Service name logo' },
}}
utilities={[
  {
    type: 'button',
    iconName: 'notification',
    ariaLabel: 'Notifications',
    badge: true,
    disableUtilityCollapse: true,
  },
  { type: 'button', iconName: 'settings', title: 'Settings', ariaLabel: 'Settings' },
  {
    type: 'menu-dropdown',
    text: 'Customer name',
    description: 'customer@example.com',
    iconName: 'user-profile',
    items: profileActions,
  },
]}
/>)
}