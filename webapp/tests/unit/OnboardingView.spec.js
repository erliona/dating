import { describe, it, expect, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import { createPinia } from 'pinia'
import OnboardingView from '@/views/OnboardingView.vue'

// Mock composables
vi.mock('@/composables/useTelegram', () => ({
  useTelegram: () => ({
    hapticFeedback: vi.fn()
  })
}))

vi.mock('@/composables/useApi', () => ({
  useApi: () => ({
    api: {
      patch: vi.fn().mockResolvedValue({})
    }
  })
}))

describe('OnboardingView', () => {
  it('progresses through steps correctly', async () => {
    const pinia = createPinia()
    const wrapper = mount(OnboardingView, {
      global: {
        plugins: [pinia]
      }
    })
    
    expect(wrapper.vm.currentStep).toBe(1)
    
    // Заполнить данные и перейти дальше
    wrapper.vm.formData = {
      name: 'Test',
      birth_date: '2000-01-01',
      gender: 'male',
      orientation: 'female'
    }
    
    await wrapper.vm.nextStep()
    expect(wrapper.vm.currentStep).toBe(2)
  })
  
  it('auto-saves progress on step change', async () => {
    const pinia = createPinia()
    const mockApi = { patch: vi.fn().mockResolvedValue({}) }
    
    const wrapper = mount(OnboardingView, {
      global: {
        plugins: [pinia],
        mocks: {
          api: mockApi
        }
      }
    })
    
    // Set up form data
    wrapper.vm.formData = {
      name: 'Test',
      birth_date: '2000-01-01',
      gender: 'male',
      orientation: 'female'
    }
    
    await wrapper.vm.nextStep()
    expect(mockApi.patch).toHaveBeenCalledWith('/profiles/progress', expect.any(Object))
  })
  
  it('restores progress on mount', async () => {
    const pinia = createPinia()
    const mockUserStore = {
      user: { id: 1 },
      profile: {
        name: 'Test User',
        current_step: 3
      }
    }
    
    const wrapper = mount(OnboardingView, {
      global: {
        plugins: [pinia]
      }
    })
    
    // Mock user store
    wrapper.vm.userStore = mockUserStore
    
    await wrapper.vm.$nextTick()
    
    expect(wrapper.vm.formData.name).toBe('Test User')
    expect(wrapper.vm.currentStep).toBe(3)
  })
  
  it('validates canProceed for each step', () => {
    const pinia = createPinia()
    const wrapper = mount(OnboardingView, {
      global: {
        plugins: [pinia]
      }
    })
    
    // Step 1 validation
    wrapper.vm.currentStep = 1
    wrapper.vm.formData = {
      name: 'Test',
      birth_date: '2000-01-01',
      gender: 'male',
      orientation: 'female'
    }
    expect(wrapper.vm.canProceed).toBe(true)
    
    // Step 1 incomplete
    wrapper.vm.formData = {
      name: '',
      birth_date: '',
      gender: '',
      orientation: ''
    }
    expect(wrapper.vm.canProceed).toBe(false)
  })
})
