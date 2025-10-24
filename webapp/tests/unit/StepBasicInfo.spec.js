import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import StepBasicInfo from '@/components/onboarding/StepBasicInfo.vue'

describe('StepBasicInfo', () => {
  it('validates name minimum length', () => {
    const wrapper = mount(StepBasicInfo, {
      props: {
        modelValue: {
          name: 'A',
          birth_date: '2000-01-01',
          gender: 'male',
          orientation: 'female'
        }
      }
    })
    
    // Проверить что кнопка disabled при коротком имени
    expect(wrapper.vm.isValid).toBe(false)
  })
  
  it('validates age requirement (18+)', () => {
    const today = new Date()
    const seventeenYearsAgo = new Date(today.getFullYear() - 17, today.getMonth(), today.getDate())
    
    const wrapper = mount(StepBasicInfo, {
      props: {
        modelValue: {
          name: 'Test',
          birth_date: seventeenYearsAgo.toISOString().split('T')[0],
          gender: 'male',
          orientation: 'female'
        }
      }
    })
    
    // Проверить что показывается ошибка
    wrapper.vm.validateForm()
    expect(wrapper.vm.errors.birth_date).toBeTruthy()
  })
  
  it('emits next event when valid', async () => {
    const wrapper = mount(StepBasicInfo, {
      props: {
        modelValue: {
          name: 'Valid Name',
          birth_date: '2000-01-01',
          gender: 'male',
          orientation: 'female'
        }
      }
    })
    
    await wrapper.vm.handleNext()
    expect(wrapper.emitted('next')).toBeTruthy()
  })
  
  it('does not emit next when invalid', async () => {
    const wrapper = mount(StepBasicInfo, {
      props: {
        modelValue: {
          name: 'A', // Too short
          birth_date: '2000-01-01',
          gender: 'male',
          orientation: 'female'
        }
      }
    })
    
    await wrapper.vm.handleNext()
    expect(wrapper.emitted('next')).toBeFalsy()
  })
  
  it('emits update:modelValue when form data changes', async () => {
    const wrapper = mount(StepBasicInfo, {
      props: {
        modelValue: {
          name: '',
          birth_date: '',
          gender: '',
          orientation: ''
        }
      }
    })
    
    // Simulate form data change
    wrapper.vm.formData.name = 'Test Name'
    
    // Check if update:modelValue was emitted
    expect(wrapper.emitted('update:modelValue')).toBeTruthy()
  })
})
